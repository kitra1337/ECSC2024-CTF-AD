<?php

class HSM {
	private $host;
	private $port;

	private $sock;

	private function __construct() {
		$this->host = getenv( 'HSM_HOST' );
		$this->port = getenv( 'HSM_PORT' );

		$error_msg = null;
		$error_code = null;

		$this->sock = fsockopen( $this->host, $this->port, $error_code, $error_msg );

		if ( ! $this->sock ) {
			throw new HSMException( $error_msg, $error_code );
		}

	}
	public function __destruct() {
		fclose( $this->sock );
	}

	public function write( $command ) {
		fwrite( $this->sock, $command );
	}

	public function read() {
        
		$response = fgets( $this->sock );
        if($response == ''){
            throw new HSMException('No response from HSM');
        }
		$parts = explode( ' ', $response );
		$response = [ 
			'status' => $parts[0],
			'msg' => $parts[1] != '' ? base64_decode( $parts[1] ) : ''
		];

		return (object) $response;
	}

	public static function importKey( $key_id, $key ) {
		$key_b64 = base64_encode( $key );

		$command = "IMPORT_KEY $key_id $key_b64\n";
        
		$HSM = new HSM();
		$HSM->write( $command );
        
		$response = $HSM->read();

		if ( $response->status != 'OK' ) {
			throw new HSMException( $response->msg );
		}

	}

	public static function importItem( $item_id, $key_id, $item_data ) {
		$item_b64 = base64_encode( $item_data );

		$command = "IMPORT_ITEM $item_id $key_id $item_b64\n";

		$HSM = new HSM();
		$HSM->write( $command );

		$response = $HSM->read();

		if ( $response->status != 'OK' ) {
			throw new HSMException( $response->msg );
		}

	}

	public static function getItem( $item_id, $key_id, $share_token ) {
		$share_token_b64 = base64_encode( $share_token );

		$command = "GET_ITEM $item_id $key_id $share_token_b64\n";

		$HSM = new HSM();
		$HSM->write( $command );

		$response = $HSM->read();

		if ( $response->status != 'OK' ) {
			throw new HSMException( $response->msg );
		}
		return $response->msg;
	}
}
