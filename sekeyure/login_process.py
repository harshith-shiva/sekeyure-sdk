import database



# Thresholds
ENROLL_MIN        = 5     # silent collection phase
IFOREST_MIN       = 30    # switch to Isolation Forest
GAUSSIAN_STORE_THRESHOLD  = 0.70   # minimum score to store during Gaussian phase
IFOREST_STORE_THRESHOLD   = 0.80   # minimum score to store during Isolation Forest phase

def process_login(user_id: str, vector, password_length: int) -> dict:

    count = database.get_sample_count(user_id)
    phase = database.get_phase(count)

    # ── Phase 1: Silent enrollment ──────────────────────────────────────────
    # No model yet, no basis for comparison
    # Store everything to build initial baseline
    if phase == "enrolling":
        database.store_sample(user_id, vector, password_length)
        new_count = count + 1

        # On hitting the threshold, train the first Gaussian model immediately
        # so it is ready for the very next login
        if new_count == ENROLL_MIN:
            X = database.load_all_vectors(user_id)
            database.train_and_store_gaussian(user_id, X, new_count)

        return {
            "verdict":           "enrolling",
            "samples_collected":  new_count,
            "samples_needed":     ENROLL_MIN,
            "message":           f"Building profile ({new_count}/{ENROLL_MIN})"
        }

    # ── Phase 2: Gaussian scoring ───────────────────────────────────────────
    if phase == "gaussian":
        model_row = database.load_model(user_id)
        score     = database.score_gaussian(vector, model_row)

        if score >= GAUSSIAN_STORE_THRESHOLD:
            # Consistent with profile — store and retrain
            database.store_sample(user_id, vector, password_length)
            new_count = count + 1
            X         = database.load_all_vectors(user_id)

            # Check if we now have enough to graduate to Isolation Forest
            if new_count >= IFOREST_MIN:
                database.train_and_store_iforest(user_id, X, new_count)
            else:
                database.train_and_store_gaussian(user_id, X, new_count)

            return {
                "verdict":           "pass",
                "score":              round(score, 4),
                "phase":             "gaussian",
                "stored":             True,
                "samples_collected":  new_count
            }

        else:
            # Suspicious or noisy — score and report but do not store
            verdict = "flag"  if score >= GAUSSIAN_STORE_THRESHOLD * 0.6 else "block"

            return {
                "verdict":  verdict,
                "score":    round(score, 4),
                "phase":   "gaussian",
                "stored":   False,
                "message": "Sample not stored — score below quality threshold"
            }

    # ── Phase 3: Isolation Forest scoring ──────────────────────────────────
    if phase == "iforest":
        model_row = database.load_model(user_id)
        score     = database.score_iforest(vector, model_row)

        if score >= IFOREST_STORE_THRESHOLD:
            # High confidence — store and periodically retrain
            database.store_sample(user_id, vector, password_length)
            new_count = count + 1

            # Don't retrain on every single login — expensive
            # Retrain every 10 new samples
            if new_count % 10 == 0:
                X = database.load_all_vectors(user_id)
                database.train_and_store_iforest(user_id, X, new_count)

            return {
                "verdict":           "pass",
                "score":              round(score, 4),
                "phase":             "iforest",
                "stored":             True,
                "samples_collected":  new_count
            }

        else:
            verdict = "flag" if score >= IFOREST_STORE_THRESHOLD * 0.6 else "block"

            return {
                "verdict":  verdict,
                "score":    round(score, 4),
                "phase":   "iforest",
                "stored":   False,
                "message": "Anomaly detected — sample not stored"
            }