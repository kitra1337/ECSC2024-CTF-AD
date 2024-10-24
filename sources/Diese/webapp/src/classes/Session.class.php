<?php

class Session {

	private static $instance = null;
	private $user = null;

	private function __construct() {
		session_start();

		if ( isset( $_SESSION['user'] ) ) {
			$this->user = $_SESSION['user'];
		}


	}

	public static function init() {
		if ( self::$instance == null ) {
			self::$instance = new Session();
		}
	}

	public static function getUser() {
		self::init();

		return self::$instance->user;
	}

	public static function getUserId() {
		self::init();

		return self::$instance->user->getId();
	}

	public static function setUser( $user ) {
		self::init();
		self::$instance->user = $user;
	}

	public function __destruct(){
		$_SESSION['user'] = self::$instance->user;
	}

	public static function isLogged() {
		self::init();
		return self::$instance->user !== null;
	}

	public static function destroy() {
		Session::init();
		self::setUser(null);
		session_destroy();
		unset($_SESSION['user']);
		self::$instance->user = null;
	}


}
