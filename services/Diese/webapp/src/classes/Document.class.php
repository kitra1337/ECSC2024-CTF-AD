<?php


class Document {
	private $id;
	private $title;
	private $body;
	private $userId;

	private $date;
	private $template;

	private $shared = false;


	public function __construct( $id, $userId, $title, $body, $date, $template ) {
		$this->id = $id;
		$this->userId = $userId;
		$this->title = $title;
		$this->body = $body;
		$this->date = $date;
		$this->template = $template;
	}

	public function getId() {
		return $this->id;
	}

	public function setId( $id ) {
		$this->id = $id;
	}

	public function getUserId() {
		return $this->userId;
	}

	public function setUserId( $userId ) {
		$this->userId = $userId;
	}

	public function getTitle() {
		return $this->title;
	}

	public function setTitle( $title ) {
		$this->title = $title;
	}

	public function getBody() {
		return $this->body;
	}

	public function setBody( $body ) {
		$this->body = $body;
	}

	public function getDate() {
		return $this->date;
	}

	public function setDate( $date ) {
		$this->date = $date;
	}
	public function setShared() {
		$this->shared = true;
	}

	public function getTemplate() {
		return Template::getById( $this->template, $this->shared );
	}

	private static function getPDO() {
		return DB::getInstance()->getConnection();
	}

	public static function create( $userId, $title, $body, $template ) {
		$pdo = self::getPDO();
		$sql = "INSERT INTO documents (user_id, title, body, date, template_id) 
                VALUES (:user_id, :title, :body, NOW(), :template) RETURNING id";
		$stmt = $pdo->prepare( $sql );
		$stmt->bindParam( ':user_id', $userId, PDO::PARAM_INT );
		$stmt->bindParam( ':title', $title );
		$stmt->bindParam( ':body', $body );
		$stmt->bindParam( ':template', $template );
		$stmt->execute();

		return $stmt->fetchColumn();
	}

	public static function getById( $id ) {
		$pdo = self::getPDO();
		$sql = "SELECT * FROM documents WHERE id = :id";
		$stmt = $pdo->prepare( $sql );
		$stmt->bindParam( ':id', $id, PDO::PARAM_INT );
		$stmt->execute();
		$data = $stmt->fetch( PDO::FETCH_ASSOC );

		if ( $data ) {
			return new self(
				$data['id'],
				$data['user_id'],
				$data['title'],
				$data['body'],
				$data['date'],
				$data['template_id']
			);
		}

		return null;
	}

	public static function getAll( $userId = null ) {
		$pdo = self::getPDO();
		if ( $userId !== null ) {
			$sql = "SELECT * FROM documents WHERE user_id = :user_id";
			$stmt = $pdo->prepare( $sql );
			$stmt->bindParam( ':user_id', $userId, PDO::PARAM_INT );
			$stmt->execute();
		} else {
			$sql = "SELECT * FROM documents";
			$stmt = $pdo->query( $sql );
		}

		$documents = [];
		while ( $data = $stmt->fetch( PDO::FETCH_ASSOC ) ) {
			$document = new self(
				$data['id'],
				$data['user_id'],
				$data['title'],
				$data['body'],
				$data['date'],
				$data['template_id']
			);
			$documents[] = $document;
		}

		return $documents;
	}

	public static function getByToken( $token) {
		$user = Session::getUser();

		if ( ! $user->verify_share( $token ) ) {
			throw new DocumentException( 'Permission Denied' );
		}

		[ $data, $t ] = explode( '.', $token, 2 );

		$data = base64_decode( $data );
		$params = [];

		parse_str( $data, $params );

		return self::getById( $params['doc_id']  );
	}

	public static function write_secret( $document ) {
		$pdo = self::getPDO();

		$key_id = Session::getUser()->getKeyId();

		$query = 'INSERT INTO secret_documents(key_id) VALUES ( :key_id ) RETURNING id';
		$stm = $pdo->prepare( $query );

		try {
			$stm->execute( [ "key_id" => $key_id ] );
		} catch (PDOException $e) {
			throw new DocumentException( "Database error" );
		}

		$item_id = $stm->fetchColumn();
		HSM::importItem( $item_id, $key_id, $document );
		return $item_id;
	}

	public static function read_secret( $item_id, $token ) {
		$key_id = Session::getUser()->getKeyId();

		return HSM::getItem( $item_id, $key_id, $token );

	}


}
