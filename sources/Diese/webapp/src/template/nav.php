<?php
// icona del doge con le notifiche
// prendi notifiche da notifications.php in ajax
?>

<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>Diese - Venetian Renaissance App</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* Custom Tailwind Config for Venetian Red */
        @layer base {
            .venetian-red {
                --tw-bg-opacity: 1;
                background-color: rgba(179,11,0, var(--tw-bg-opacity)) !important;
            }

            .venetian-red-text {
                --tw-text-opacity: 1;
                color: rgba(179,11,0, var(--tw-text-opacity));
            }
        }
    </style>
</head>

<body class="bg-white font-sans leading-normal tracking-normal h-screen flex flex-col">
    <!-- Navbar -->
    <nav class="venetian-red p-6">
        <div class="container mx-auto flex justify-between items-center">
            <!-- Logo Placeholder -->
            <div class="flex items-center">
                <img src="/template/logo.jpeg" alt="Diese Logo" class="mr-3" width="50" height="50"> <!-- Placeholder logo -->
                <div class="text-white text-2xl font-bold"><a href="/">Diese</a></div>
            </div>
            <ul class="flex space-x-6 text-white">
                <?php if (Session::isLogged()) { ?>
                    <li><a href="/write.php" class="hover:text-gray-300">Write</a></li>
                    <li><a href="/list.php" class="hover:text-gray-300">List</a></li>
                    <li><a href="/write_secret.php" class="hover:text-gray-300">Write secret</a></li>
                    <li><a href="/create_template.php" class="hover:text-gray-300">New Template</a></li>
                    <li><a href="/settings.php" class="hover:text-gray-300">Settings</a></li>
                    <li><a href="/logout.php" class="hover:text-gray-300">Logout</a></li>
                    <li class="font-bold">Welcome back, <?= Session::getUser()->getUsername(); ?></li>
                <?php } else { ?>
                    <li><a href="/login.php" class="hover:text-gray-300">Login</a></li>
                    <li><a href="/register.php" class="hover:text-gray-300">Register</a></li>
                <?php } ?>
            </ul>
        </div>
    </nav>