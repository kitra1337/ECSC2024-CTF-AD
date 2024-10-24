<?php
include 'classes/autoload.php';

if (! Session::isLogged()) {
	header('/login.php');
	die();
}


if (Request::issetFile('document')) {
	$document = Request::file('document')->readFile();
	try {
		$item_id = Document::write_secret($document);
	} catch (UserException | DocumentException | HSMException $e) {
		$error_msg = $e->getMessage();
	}
}

require 'template/nav.php';
?>

<section class="bg-white flex flex-col items-center text-center my-10 grow">
	<h2 class="text-4xl md:text-5xl venetian-red-text font-extrabold mb-4">Write your secret</h2>

	<?php if (isset($error_msg)) : ?>
		<p class="error"><?= $error_msg; ?></p>
	<?php endif; ?>

	<form class="bg-gray-200 p-8 rounded-lg shadow-md w-full max-w-sm" method="POST" action="" enctype="multipart/form-data">
		<div class="mb-4">
			<label for="document" class="block text-left font-semibold mb-2 venetian-red-text">Your secret</label>
			<input type="file" name="document" id="document">
		</div>

		<button type="submit" class="px-8 py-3 text-white font-semibold rounded-lg shadow-md transition duration-300 w-full venetian-red">Upload</button>

		<?php

		if (isset($item_id)) {
			echo "Item ID: <b>$item_id</b>";
		}
		?>
	</form>
</section>

<?php require 'template/footer.php'; ?>