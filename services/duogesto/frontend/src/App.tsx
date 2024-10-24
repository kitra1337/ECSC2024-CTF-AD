import './App.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import { HashRouter, Route, Routes } from 'react-router-dom';
import NavigationBar from './components/NavigationBar';
import HomePage from './components/HomePage';
import Login from './components/Login';
import Logout from './components/Logout';
import Profile from './components/Profile';
import Quiz from './components/Quiz';
import CreateChallenge from './components/CreateChallenge';
import UserChallenges from './components/UserChallenges';
import Friends from './components/Friends';
import { useState } from 'react';

function App() {

  const[loggedIn, setLoggedIn] = useState<boolean>(false);
  const[username, setUsername] = useState<string>('');

  return (
    <HashRouter>
      <NavigationBar loggedIn={loggedIn} setLoggedIn={setLoggedIn} setUsername={setUsername} />
      <Routes>
        <Route path='/' element={<HomePage loggedIn={loggedIn} />} />
        <Route path='/login' element={<Login loggedIn={loggedIn} setLoggedIn={setLoggedIn} />} />
        <Route path='/logout' element={<Logout setLoggedIn={setLoggedIn} />} />
        <Route path='/profile' element={<Profile username={username} />} />
        <Route path='/quiz' element={<Quiz />} />
        <Route path='/createchall' element={<CreateChallenge />} />
        <Route path='/userchall' element={<UserChallenges />} />
        <Route path='/friends' element={<Friends />} />
      </Routes>
    </HashRouter>
  );
}

export default App;
