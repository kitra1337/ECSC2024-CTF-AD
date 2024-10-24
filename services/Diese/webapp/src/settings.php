<?php
include 'classes/autoload.php';

if (! Session::isLogged()) {
	header('Location: /login.php');
	die();
}


if (Request::issetFile('key')) {
	$key = Request::file('key')->readFile();
	try {
		$imported_key = Session::getUser()->importKey($key);
	} catch (UserException | HSMException $e) {
		$error_msg = $e->getMessage();
	}
}

require 'template/nav.php';
?>

<section class="bg-white flex flex-col items-center text-center my-10 grow">
	<h2 class="text-4xl md:text-5xl venetian-red-text font-extrabold mb-4">Upload settings</h2>

	<?php if (isset($error_msg)) : ?>
		<p class="error"><?= $error_msg; ?></p>
	<?php endif; ?>

	<form class="bg-gray-200 p-8 rounded-lg shadow-md w-full max-w-sm" method="POST" action="" enctype="multipart/form-data">
		<div class="mb-4">
			<label for="key" class="block text-left font-semibold mb-2 venetian-red-text">Key file</label>
			<input type="file" name="key" id="key">
		</div>

		<button type="submit" class="px-8 py-3 text-white font-semibold rounded-lg shadow-md transition duration-300 w-full venetian-red">Upload</button>

		<?php
		if (isset($imported_key)) {
			echo "Imported key ID: <b>$imported_key</b>\n";
		}
		?>
	</form>
</section>

<?php require 'template/footer.php'; ?>