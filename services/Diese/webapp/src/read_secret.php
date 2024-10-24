<?php
include 'classes/autoload.php';

if ( ! Session::isLogged() ) {
	header( '/login.php' );
	die();
}

if (Request::issetFile('share_token' ) && Request::issetPost('item_id') ) {
	$token = Request::file('share_token')->readFile();
	$item_id = Request::post('item_id')->getInt();
	try {
		$document = Document::read_secret( $item_id, $token );
	} catch (UserException | HSMException $e) {
		$error_msg = $e->getMessage();
	}
}

if ( isset( $error_msg ) ) {
    header('HTTP/1.1 500 Server Error');
	echo $error_msg;
} else {
	echo $document;
}

?>