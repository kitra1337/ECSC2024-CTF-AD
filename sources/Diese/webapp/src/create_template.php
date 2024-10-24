<?php
include 'classes/autoload.php';

if(!Session::isLogged()){
    header('Location: /login.php');
    die();
}

if(Request::issetPost('name', 'template')){
    $name = Request::post('name')->getString();
    $template = Request::post('template')->getString();
    
    Template::create($name, $template);
    header("Location: /write.php");
    die();
}

require 'template/nav.php';
?>

<section class="bg-white flex flex-col items-center justify-center text-center my-10 grow">
	<h2 class="text-4xl md:text-5xl venetian-red-text font-extrabold mb-4">Add a template</h2>

	<form class="bg-gray-200 p-8 rounded-lg shadow-md w-full max-w-sm" method="POST" action="">
		<div class="mb-4">
			<label for="name" class="block text-left font-semibold mb-2 venetian-red-text">Template Name</label>
			<input type="text" id="name" name="name" required class="border border-gray-300 rounded-lg p-2 w-full" placeholder="Enter the template name">
		</div>
		<div class="mb-4">
			<label for="template" class="block text-left font-semibold mb-2 venetian-red-text">Template</label>
			<textarea id="template" name="template" rows="10" cols="50" class="border border-gray-300 rounded-lg p-2 w-full" placeholder="Write a document template here. You can use different tags to place elements around. For example:
{body} : The body of the document
{title} : The title of the document
{author} : The name of the author of the document
{date} : The date of the document
                
You can also use the tag auto_share, that will automagically share the document with your favorite patrician magistrate! The format is
{auto_share=[to_user=*username*&message=*some text*]}

Last but not least, you can add flavour using HTML.
            "required></textarea>
		</div>

		<button type="submit" class="px-8 py-3 text-white font-semibold rounded-lg shadow-md transition duration-300 w-full venetian-red">Add</button>
	</form>
</section>

<?php require 'template/footer.php'; ?>
