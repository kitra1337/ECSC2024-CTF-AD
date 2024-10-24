<?php
include 'classes/autoload.php';

if (! Session::isLogged()) {
	header('Location: /login.php');
	die();
}

if (! (Request::issetGet('token') || Request::issetGet('id'))) {
	header('Location: /');
	die();
}

if (Request::issetGet('token')) {
	$token = Request::get('token')->getString();
	$document = Document::getByToken($token);
	$document->setShared();
} else if (Request::issetGet('id')) {
	try {
		$document = Document::getById(Request::get('id')->getInt());
	} catch (DocumentException $e) {
		header("HTTP/1.1 404 Not Found");
		die();
	}
	if ($document->getUserId() !== Session::getUserId()) {
		header("HTTP/1.1 404 Not Found");
		die();
	}
}

$template = $document->getTemplate();
$document = $template->render($document, false);

require 'template/nav.php';
?>


<section class="bg-white flex flex-col items-center text-center mt-10 grow h-full justify-between">
	<div>
		<h2 class="text-4xl md:text-5xl venetian-red-text font-extrabold mb-4"><?php echo $document->getTitle(); ?> </h2>

		<p>
			<?php echo $document->getBody(); ?>
		</p>

	</div>

	<div id="sharing-view">
		<form action="/share.php" method="POST" class="flex flex-row relative bottom-10">
			<div class="">
				<input type="text" id="to" name="to" class="border border-gray-300 p-2 w-full" placeholder="username you want to share to" required>
				<input type="hidden" name="document" id="document_id" value="<?php echo Request::get('id')->getInt(); ?>">
			</div>
			<button type="submit" class="text-white font-semibold shadow-md transition duration-300 venetian-red block" width="30px" height="30px" id="share-button">
				<img src="/template/share.png" width="30px" height="30px" alt="">
			</button>
		</form>
	</div>

	<script>
		document.getElementById("share-button").addEventListener("click", async function(e) {
			e.preventDefault();

			const to = document.getElementById("to").value;
			const document_id = document.getElementById("document_id").value;

			const response = await fetch(`/share.php`, {
				method: "POST",
				headers: {
					"Content-Type": "application/x-www-form-urlencoded",
				},
				body: `to=${to}&document=${document_id}`,
			});
			const content = await response.json();

			if (content.error) {
				alert(content.error);
				return;
			}

			document.getElementById("sharing-view").innerHTML = `<p class="py-10 font-bold">Shared with token: ${content.token}</p>`;
		});
	</script>
</section>

<?php require 'template/footer.php'; ?>

<?php

// aggiungi form POST su /share.php passando to (utente corrente session::getUser()->getUsername()) e document (id del documento Request::get( 'id' )->getInt()), 