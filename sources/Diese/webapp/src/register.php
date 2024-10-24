<?php
include 'classes/autoload.php';

if(Session::isLogged()){
    header('Location: /');
    die();
}

if ( Request::issetPost('username', 'password') ) {
	try {
        $username = Request::post('username')->getString();
        $password = Request::post('password')->getString();
		$user = User::register( $username, $password );
		Session::setUser($user);
        header('Location: /');
        die();
	} catch (UserException|UnexpectedValueException $e) {
		$error_msg = $e->getMessage();
	}
}

require 'template/nav.php';


?>

<section class="bg-white flex flex-col items-center justify-center text-center my-10 grow">
	<h2 class="text-4xl md:text-5xl venetian-red-text font-extrabold mb-4">Register to Diese</h2>

	<?php if (isset($error_msg)) : ?>
		<div class="bg-red-500 text-white p-4 rounded-lg mb-4 hidden" id="error-box">
			<p id="error-message"><?= $error_msg; ?></p>
		</div>
	<?php endif; ?>

	<form class="bg-gray-200 p-8 rounded-lg shadow-md w-full max-w-sm" method="POST" action="">
		<div class="mb-4">
			<label for="username" class="block text-left font-semibold mb-2 venetian-red-text">Username</label>
			<input type="text" id="username" name="username" required class="border border-gray-300 rounded-lg p-2 w-full" placeholder="Enter your username">
		</div>
		<div class="mb-4">
			<label for="password" class="block text-left font-semibold mb-2 venetian-red-text">Password</label>
			<input type="password" id="password" name="password" required class="border border-gray-300 rounded-lg p-2 w-full" placeholder="Enter your password">
		</div>
		<button type="submit" class="px-8 py-3 text-white font-semibold rounded-lg shadow-md transition duration-300 w-full venetian-red">Login</button>
	</form>
	<p class="mt-4 text-gray-600">Do you already have an account? <a href="/login.php" class="text-venetian-red hover:underline">Login here</a></p>
</section>

<?php require 'template/footer.php'; ?>
