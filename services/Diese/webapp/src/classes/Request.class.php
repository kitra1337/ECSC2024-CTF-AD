<?php

class Param {

	private $tpe;
	private $name;
	private $value;

	public function __construct( $name, $value, $type ) {
		$this->name = $name;
		$this->value = $value;
		$this->type = $type;
	}

	public function getString() {
		try {
			return Utils::getString( $this->value );
		} catch (UnexpectedValueException) {
			throw new UnexpectedValueException( $this->name . ": not a string." );
		}
	}

	public function getInt() {
		try {
			return Utils::getInteger( $this->value );
		} catch (UnexpectedValueException) {
			throw new UnexpectedValueException( $this->name . ": not an integer." );
		}

	}

	public function readFile() {
		$file = file_get_contents( $this->value['tmp_name'] );
        if(strlen($file) > 1024*2){
            throw new UnexpectedValueException( $this->name . ": Upload file too big." );
        }
        return $file;
	}

}

class Request {

	public static function issetPost( ...$names ) {
		foreach ( $names as $name ) {
			if ( ! isset( $_POST[ $name ] ) ) {
				return false;
			}
		}

		return true;
	}

	public static function issetGet( ...$names ) {
		foreach ( $names as $name ) {
			if ( ! isset( $_GET[ $name ] ) ) {
				return false;
			}
		}
		return true;
	}

	public static function issetFile( ...$names ) {
		foreach ( $names as $name ) {
			if ( ! isset( $_FILES[ $name ] ) ) {
				return false;
			}
		}
		return true;
	}

	public static function post( $name ) {
		if ( isset( $_POST[ $name ] ) )
			return new Param( $name, $_POST[ $name ], 'POST' );
		return false;

	}

	public static function get( $name ) {
		if ( isset( $_GET[ $name ] ) )
			return new Param( $name, $_GET[ $name ], 'GET' );
		return false;
	}

	public static function file( $name ) {
		if ( isset( $_FILES[ $name ] ) ) {
			return new Param( $name, $_FILES[ $name ], 'FILES' );
		}
	}
}