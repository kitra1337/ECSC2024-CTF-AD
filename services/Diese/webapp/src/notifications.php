<?php

include 'classes/autoload.php';

if(!Session::isLogged()){
    header('Location: /');
    die();
}

echo json_encode(['notifications' =>  Session::getUser()->getNotifications()]);