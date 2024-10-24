<?php


include 'classes/autoload.php';

if(!Session::isLogged()){
    header('Location: /login.php');
    die();
}

if(Request::issetGet('id')){
    $id = Request::get('id')->getInt();
    try{
        $template = Template::getById($id);
    }catch(TemplateNotFoundException $e){
        header('HTTP/1.0 404 Template not found');
        die();
    }
    $template = Template::getById($id);
    
    echo json_encode([
        "name" => $template->getName(),
        "template" => $template->getTemplate()]
    );
    
}else{
    header('HTTP/1.0 404 Template not found');
    die();
}

