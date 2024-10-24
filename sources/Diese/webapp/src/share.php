<?php

include 'classes/autoload.php';

if ( ! Session::isLogged() ) {
	header( 'Location: /' );
	die();
}


if ( Request::issetPost( 'to', 'document' ) ) {
	$data = [ 
		'to_user' => Request::post( 'to' )->getString(),
		'from_user' => Session::getUserId(),
		'doc_id' => Request::post( 'document' )->getInt()
	];
	
	try {
		$to_user = User::getUserByUsername( $data['to_user'] );
		$token = Session::getUser()->sign_share( $data );

		$notification_text = "<a href='/read.php?token=$token'>User " . Session::getUser()->getUsername() . " shared a document with you.";
		$to_user->notify( $notification_text );

	} catch (UserNotFoundException | UserException | DocumentException $e) {
		$to_ret = [ 'status' => false, 'error' => $e->getMessage() ];
		die( json_encode( $to_ret ) );
	}

	die( json_encode( [ 'status' => true, 'token' => $token ] ) );
}