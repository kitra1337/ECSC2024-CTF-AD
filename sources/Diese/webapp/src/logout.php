<?php

include 'classes/autoload.php';

if(Session::isLogged()){
    Session::destroy();
}


header('Location: /');