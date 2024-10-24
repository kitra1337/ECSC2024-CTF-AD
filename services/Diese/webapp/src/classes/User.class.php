<?php

class UserException extends Exception {
}

class User {
	private $username;
	private $id;

    private $password_hash;

	private function __construct( $id, $username, $password_hash ) {
		$this->id = $id;
        $this->username = $username;
		$this->password_hash = $password_hash;
	}

	public static function register( $username, $password ) {
		
        try{
            self::getUserByUsername($username);
            throw new UserException("User already registered");
        }catch(UserNotFoundException $e){
            
        }

        $pdo = DB::getInstance()->getConnection();
        
        $query = 'INSERT INTO users(username, password_hash) VALUES (:username, :password)';
        $stm = $pdo->prepare($query);

        $password_hash = password_hash($password, PASSWORD_DEFAULT);
        try{
            $stm->execute(['username'=>$username, 'password'=>$password_hash]);
        }
        catch(PDOException $e){
            throw new UserException("User already registered");
        }

		return self::getUserByUsername($username);
	}

	public static function login( $username, $password ) {
		
        try{
            $user = self::getUserByUsername($username);
        }catch(UserNotFoundException $e){
            throw new UserException('Wrong username or password');
        }

        $password_hash = $user->getPassword();

        if(!$password_hash || !password_verify($password, $password_hash)){
            throw new UserException('Wrong username or password');
        }
		return $user;
	}

    public static function getUserById($id){
        $sql = "SELECT * FROM users WHERE id = :id";

        $pdo = DB::getInstance()->getConnection();

        $stm = $pdo->prepare($sql);
        $stm->execute(['id'=>$id]);

        $data = $stm->fetch(PDO::FETCH_OBJ);
        
        if(!$data){
            throw new UserNotFoundException("Cannot find user with id $id");
        }
        $user = new User($data->id, $data->username, $data->password_hash);

        return $user;
    }

    public static function getUserByUsername($username){
        $sql = "SELECT * FROM users WHERE username = :username";

        $pdo = DB::getInstance()->getConnection();
        $stm = $pdo->prepare($sql);
        $stm->execute(['username'=>$username]);

        $data = $stm->fetch(PDO::FETCH_OBJ);
        
        if(!$data){
            throw new UserNotFoundException("Cannot find user with username '$username'");
        }
        $user = new User($data->id, $data->username, $data->password_hash);

        return $user;
    }

    public function importKey($key){
        $query = 'INSERT INTO user_keys(user_id) VALUES (:user_id) RETURNING id';

        $pdo = DB::getInstance()->getConnection();

        $stm = $pdo->prepare($query);
        try{
            $stm->execute(['user_id'=>$this->id]);
        }catch(PDOException $e){
            throw new UserException('Cannot import key');
        }

        $key_id = $stm->fetchColumn();
        HSM::importKey($key_id, $key);
        
        return $key_id;

    }

    public function getKeyId(){
        $query = 'SELECT id FROM user_keys WHERE user_id = :user_id';

        $pdo = DB::getInstance()->getConnection();

        $stm = $pdo->prepare($query);
        try{
            $stm->execute(['user_id'=>$this->id]);
        }catch(PDOException $e){
            throw new UserException('Cannot get key');
        }

        $key_id = $stm->fetchColumn();
        if(!$key_id){
            throw new UserException('Cannot get key');
        }

        return $key_id;
    }

	public function getId() {
		return $this->id;
	}

	public function getUsername() {
		return $this->username;
	}

    public function getPassword(){
        return $this->password_hash;
    }

    public function getDocuments(){
        return Document::getAll($this->id);
    }

    public function getNotifications(){
        $query = "DELETE FROM notifications WHERE user_id = :user_id RETURNING body";

        $pdo = DB::getInstance()->getConnection();

        $stm = $pdo->prepare($query);
        try{
            $stm->execute(['user_id'=>$this->id]);
        }catch(PDOException $e){
            throw new UserException('Cannot get notifications' . $e->getMessage());
        }

        return $stm->fetchAll(PDO::FETCH_COLUMN, 0);

    }

    public function notify($body){
        $query = "INSERT INTO notifications (user_id, body) VALUES (:user_id, :body)";

        $pdo = DB::getInstance()->getConnection();

        $stm = $pdo->prepare($query);
        try{
            $stm->execute(['user_id'=>$this->id, 'body'=>$body]);
        }catch(PDOException $e){
            throw new UserException('Cannot write notification' . $e->getMessage());
        }
    }

    public function sign_share($data){
        $document = Document::getById($data['doc_id']);

        if($data['from_user'] != $this->getId() || $document->getUserId() !== $this->getId()){
            throw new UserException('Permission denied');
        }

        $payload = http_build_query($data);
        $to_sign = base64_encode($payload);
        return $to_sign . '.'. Utils::hmac($to_sign);
    }


    public function verify_share($token){
        $params = Utils::verify_hmac($token);
        return $params['to_user'] == $this->getUsername();
    }
}
