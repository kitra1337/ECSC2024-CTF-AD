<?php
include 'classes/autoload.php';

if ( ! Session::isLogged() ) {
	header( 'Location: /login.php' );
	die();
}

if ( Request::issetPost( 'title', 'body', 'template' ) ) {
	try {
		$title = Request::post( 'title' )->getString();
		$body = Request::post( 'body' )->getString();
		$template_id = Request::post( 'template' )->getInt();
		$template = Template::getById( $template_id );
	} catch (UnexpectedValueException | TemplateNotFoundException $e) {
		$error_msg = $e->getMessage();
	}
	$id = Document::create( Session::getUserId(), $title, $body, $template_id );
	$document = Document::getById( $id );

	$template->render( $document, true );
	header( "Location: /read.php?id=$id" );
	die();
}

$templates = Template::getAll();

require 'template/nav.php';
?>

<section class="bg-white flex flex-col items-center justify-center text-center my-10 grow">
	<h2 class="text-4xl md:text-5xl venetian-red-text font-extrabold mb-4">Add a document</h2>

	<form class="bg-gray-200 p-8 rounded-lg shadow-md w-full max-w-sm" method="POST" action="">
		<?php if ( isset( $error_msg ) ) : ?>
			<div class="bg-red-500 text-white p-4 rounded-lg mb-4 hidden" id="error-box">
				<p id="error-message"><?= $error_msg; ?></p>
			</div>
		<?php endif; ?>
		<div class="mb-4">
			<label for="title" class="block text-left font-semibold mb-2 venetian-red-text">Title</label>
			<input type="text" id="title" name="title" required class="border border-gray-300 rounded-lg p-2 w-full"
				placeholder="Enter your title">
		</div>
		<div class="mb-4">
			<label for="content" class="block text-left font-semibold mb-2 venetian-red-text">Content</label>
			<textarea id="content" name="body" rows="10" cols="50"
				class="border border-gray-300 rounded-lg p-2 w-full" required></textarea>
		</div>
		<label for="template" class="block text-left font-semibold mb-2 venetian-red-text">Template</label>
		<select name="template" class="border border-gray-300 rounded-lg p-2 w-full my-5">
			<?php
			foreach ( $templates as $template ) {
				echo '<option value="' . $template->getId() . '">' . $template->getName() . '</option>';
			}
			?>
		</select>

		<button type="submit"
			class="px-8 py-3 text-white font-semibold rounded-lg shadow-md transition duration-300 w-full venetian-red">Add</button>
	</form>
</section>

<?php require 'template/footer.php'; ?>