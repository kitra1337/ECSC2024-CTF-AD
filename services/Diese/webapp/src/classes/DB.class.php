<?php

class DB {
	const db_path = 'data/database.sqlite';
	private static $instance;
	private $pdo;

	private function __construct() {

		$host = getenv('DB_HOST');
		$user = getenv('DB_USER');
		$pass = getenv('DB_PASS');
		$db = "db";
		$dsn = "mysql:host=$host;dbname=$db;";

		try {
			$this->pdo = new PDO( $dsn, $user, $pass );
		} catch (PDOException $e) {
			throw new PDOException( $e->getMessage(), (int) $e->getCode() );
		}
	}

	public static function getInstance() {
		if ( self::$instance === null )
			self::$instance = new DB();

		return self::$instance;
	}

	public function getConnection() {
		return $this->pdo;
	}
}
