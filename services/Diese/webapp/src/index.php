<?php

include 'classes/autoload.php';
Session::isLogged();
require 'template/nav.php';

?>

<img src="/template/flag.svg" class="mx-auto py-5" alt="Diese Logo" class="mr-3">

<section class="bg-white flex flex-col items-center justify-center text-center my-10 grow">
	<h2 class="text-4xl md:text-5xl venetian-red-text font-extrabold mb-4">Embrace the Renaissance of Communication</h2>
	<p class="text-gray-700 text-lg md:text-xl mb-8">
	Have you seen anything that goes against the security of Republica Serenissima? Talk to us!<br>
	Diese enables common citizens to talk with their favourite venetian security council. We offer both clear text messages and HSM-encrypted messages to offer all the privacy that the (patrician) defendant needs!
	
	<p><small>We won't accept any reports about Florian's prices.</small></p>
	</p>
	<a href="/login.php" class="px-8 py-3 venetian-red text-white font-semibold rounded-lg shadow-md hover:bg-red-800 transition duration-300">Get Started</a>
</section>

<?php require 'template/footer.php'; ?>