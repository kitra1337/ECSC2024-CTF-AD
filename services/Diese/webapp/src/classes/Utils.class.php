<?php

class Utils{

    public static function getInteger($i){
        if(!is_numeric($i)){
            throw new UnexpectedValueException();
        }

        return intval($i);
    }

    public static function getString($s){
        if(!is_string($s)){
            throw new UnexpectedValueException();
        }

        return $s;
    }

    public static function hmac($s){
        $key = getenv('SHARE_SECRET');
        return sha1($key . $s);
    }

    public static function verify_hmac($token){
        [$data, $l_hmac] = explode('.', $token, 2);

        $r_hmac = Utils::hmac($data);

        if(!hash_equals($r_hmac, $l_hmac)){
            return false;
        };
        
        $data = base64_decode($data);
        $params = [];
        
        parse_str($data, $params);
        return $params;
    }

}