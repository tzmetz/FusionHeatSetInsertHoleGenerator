# FusionHeatSetInsertHoleGenerator
Contains source for automating the creation holes for heat set inserts in Fusion 360

## General 
This repository contains a Python script that uses the Autodesk Fusion 360 API for creating a custom command in Fusion that allows the user to create holes for heat set inserts on 3D printed parts

## Dependencies 
* Autodesk Fusion 360 >2.0.9011
* VS Code >1.50.0

## Setup 
* Create a new addin script in Fusion from the addins menu 
* Fill in the dialogue box for creating a new script. Make sure to toggle Python as the language for the script
* Copy this code into the newly created .py file that Fusion will automatically create 
* Copy the manifest file and resources folder in this repo to the directory that Fusion created when creating the new addin 


