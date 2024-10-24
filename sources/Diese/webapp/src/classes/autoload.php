<?php

function autoloader( $class ) {

	if ( str_contains( $class, 'Exception' ) ) {
		$path = "classes/exceptions/{$class}.class.php";
	} else {
		$path = "classes/{$class}.class.php";
	}

	if ( file_exists( $path ) )
		include $path;
}

spl_autoload_register( 'autoloader' );
