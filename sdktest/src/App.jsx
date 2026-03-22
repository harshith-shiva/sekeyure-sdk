import { useRef, useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from './assets/vite.svg'
import heroImg from './assets/hero.png'
import './App.css'

function App() {

  const keydowntimes=useRef([]);
  const keystrokes=useRef([]);
  

  const handlekeydown = (e)=> {
    if(e.key.length>1) return;

    keydowntimes.current.push(performance.now())
  }

  const handlekeyup = (e)=> {
    if (e.key.length>1) return;
    const keydown = keydowntimes.current.shift();

    keystrokes.current.push({
      index:keystrokes.current.length,
      keydowntime:keydown,
      keyuptime:performance.now()
    })
  }

  const handleSubmit = () => {
    console.log("Keystrokes:", keystrokes.current);

    // reset after logging
    keydowntimes.current = [];
    keystrokes.current = [];
  };
  
  return (
    <div>
      <input
        type="password"
        onKeyDown={handlekeydown}
        onKeyUp={handlekeyup}
        className='form-control input'

      />
      <button onClick={handleSubmit} className='btn btn-danger'>Submit</button>
    </div>
  );
}

export default App
