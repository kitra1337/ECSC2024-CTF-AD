<?php

class Template {

	private $id;
	private $template;

	private $name;
	private $user_id;

	private function __construct( $id, $name, $template, $user_id ) {
		$this->id = $id;
		$this->name = $name;
		$this->template = $template;
		$this->user_id = $user_id;
	}

	public function render( $document, $notify ) {
		$tags = [ 'title', 'body', 'date', 'author' ];
		$output = $this->template;

		foreach ( $tags as $tag ) {
			switch ( $tag ) {
				case 'title':
					$output = str_replace( "{title}", $document->getTitle(), $output );
					break;
				case 'body':
					$output = str_replace( "{body}", $document->getBody(), $output );
					break;
				case 'date':
					$output = str_replace( "{date}", $document->getDate(), $output );
					break;
				case 'author':
					$author = User::getUserById( $document->getUserId() )->getUsername();
					$output = str_replace( "{author}", $author, $output );
					break;
			}
		}
		;
		$document->setBody( $output );
		$rendered = $this->parse_settings( $document, $notify );
		$document->setBody( $rendered );
		return $document;
	}

	public function parse_settings( $document, $notify ) {
		$pattern = '/{auto_share=\[(.*?)\]}/';
		if ( ! $notify ) {
			return preg_replace( $pattern, '', $document->getBody() );
		}

		$auto_share = [];
		$output = $document->getBody();
		if ( preg_match_all( $pattern, $output, $auto_share ) ) {
			foreach ( $auto_share[1] as $share ) {
				$obj = [];

                $params = explode('&', $share);
                foreach($params as $p){
                    [$key, $value] = explode('=', $p, 2);
                    $obj[$key] = $value;
                }
				try {
					$username = $obj['to_user'] ?? null;
					$to_user = User::getUserByUsername( $username );
				} catch (UserNotFoundException) {
					throw new DocumentException( 'Can not find user in auto_share.' );
				}
				$current_user = Session::getUser();
				$obj['from_user'] = $current_user->getId();
				$obj['doc_id'] = $document->getId();

				$token = $current_user->sign_share( $obj );
				$notification = "<a href='/read.php?token=$token'>User " . Session::getUser()->getUsername() . " automatically shared a document with you.";
				if ( $obj['message'] ) {
					$notification .= "The reason is: " . $obj['message'] . "\n";
				}
				$notification .= "</a>";
				$to_user->notify( $notification );
			}
		}
		return preg_replace( $pattern, '', $output );
	}



	public static function create( $name, $template ) {
		$query = "INSERT INTO templates(name, template, user_id) VALUES (:name, :template, :user_id) RETURNING id";

		$user_id = Session::getUserId();
		if ( $user_id == NULL ) {
			throw new Exception( "Cannot overwrite default templates" );
		}

		$pdo = DB::getInstance()->getConnection();
		$stm = $pdo->prepare( $query );

		$stm->execute( [ 
			"name" => $name,
			"template" => $template,
			"user_id" => $user_id
		] );

		$id = $stm->fetchColumn();

		return new self( $id, $name, $template, $user_id );
	}

	public static function getAll() {

		$query = 'SELECT * FROM templates WHERE user_id IS NULL OR user_id = :user_id';

		$user_id = Session::getUserId();
		$pdo = DB::getInstance()->getConnection();
		$stm = $pdo->prepare( $query );

		$stm->execute( [ 
			"user_id" => $user_id
		] );

		$templates = [];
		while ( $data = $stm->fetch( PDO::FETCH_ASSOC ) ) {
			$template = new self(
				$data['id'],
				$data['name'],
				$data['template'],
				$data['user_id']
			);
			$templates[] = $template;
		}

		return $templates;

	}

	public static function getById( $id, $shared = false ) {
		$query = 'SELECT * FROM templates WHERE id = :id AND (user_id IS NULL OR user_id = :user_id)';
		$data = [ 'id' => $id ];
		if ( $shared ) {
			$query = 'SELECT * FROM templates WHERE id = :id';
		} else {
			$user_id = Session::getUserId();
			$data['user_id'] = $user_id;
		}

		$pdo = DB::getInstance()->getConnection();
		$stm = $pdo->prepare( $query );

		$stm->execute( $data );

		$data = $stm->fetch( PDO::FETCH_ASSOC );

		if ( ! $data ) {
			throw new TemplateNotFoundException();
		}

		return new self( $data['id'],
			$data['name'],
			$data['template'],
			$data['user_id'] );
	}

	public function getId() {
		return $this->id;
	}

	public function getName() {
		return $this->name;
	}

	public function getTemplate() {
		return $this->template;
	}

	public function getUserId() {
		return $this->user_id;
	}

}