<?php
include 'classes/autoload.php';

if (! Session::isLogged()) {
	header('Location: /login.php');
	die();
}

$documents = Session::getUser()->getDocuments();

require 'template/nav.php';
?>

<section class="bg-white flex flex-col items-center text-center my-10 grow">
	<h2 class="text-4xl md:text-5xl venetian-red-text font-extrabold mb-4 mt-0 pt-0">Your notes</h2>

	<ul class="list-group col-md-6 col-lg-4 my-3 mx-auto">
		<?php
		foreach ($documents as $document) {
			echo '<li class="list-group-item"><a href="/read.php?id=' . $document->getId() . '">' . $document->getTitle() . '</a></li>';
		}

		?>
	</ul>
</section>

<?php require 'template/footer.php'; ?>