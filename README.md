# Local Comic Reader Web Application

A lightweight, purely local web application for reading comics. Place your `.cbz` or `.cbr` files into organized series folders, and the application instantly builds a beautiful, interface to read them on your localhost server or mobile device on the same network.

## Features
- **Zero-Extraction Storage:** Comics `.cbz` files are opened entirely in browser memory using JSZip, saving you massive amounts of hard drive space.
- **Smart Metadata & Search:** Automatically generates `config.json` files for series. Add characters, genres, and creators to dynamically search through your library.
- **Binge Mode:** Natively detects when you are near the end of an issue and prompts you to jump into the chronological next issue.
- **Persistent Reading Tracking:** Uses browser local storage to remember which issues you've finished, graying out their covers and giving you a custom Right-Click context menu to manage read states.
- **Mobile Friendly:** Fully responsive UI, including the ability to scroll through pages using your phone's physical Volume Keys.
- **Custom Theming:** Use `preferences.json` to swap CSS styles globally.

## How to Use
1. Inside your root directory, create a directory called `./collections`. Inside this directory, create subdirectories for any comic series (e.g., `./collections/Thunderbolts/`).
2. Drop your `.cbz` or `.cbr` comic files into that directory.
3. Double-click the `RunReader.bat` file to start the application.
4. The script will automatically:
   - Run `UpdateLibrary.ps1` to scan directories, extract cover images, and update `libraryData.js` with your latest issues.
   - Boot a lightweight Python HTTP server.
   - Open your default web browser directly to the reader.

## Requirements
- **Windows / PowerShell 5+** (for dynamic library building)
- **Python 3** (for the lightweight localhost server)
- A modern Web Browser

## Architecture & How it Works
The application is entirely self-hosted. Instead of relying on a heavy database like SQL, `UpdateLibrary.ps1` runs on startup to scan raw directories using Regular Expressions, pulling out issue dates/names and injecting them into a static `libraryData.js` object. 

Python simply serves the directory over HTTP to bypass standard browser CORS limitations. All the heavy lifting—from sorting, searching, URL routing, and in-memory zip extraction—is handled natively by Vanilla JavaScript and HTML5 on the frontend!