# Stripplier
A script to apply a Source Engine Stripper .cfg to a .vmf.
## Instructions
The script reads a .vmf, .bsp, and .cfg of the same name from an input folder directory relative to where the executable is. To use the script in the intended way, do the following:
1) Create an input folder at the directory of the executable. For example if the .exe is present at .../folder, create an input folder so that .../folder/input exists
2) Place the .vmf, .bsp, and .cfg files within the input folder
   - Make sure all files have the same name including same letter cases
   - It is recommended to save the .vmf file in hammer before using script
3) Enter the name of the map when prompted in the console
   - Type in the map name only without any file extensions
4) If successful, the script will create a strippered .vmf and a log file in a separate output folder
## Navigating the log
For each stripper block the script executes, it will also write relevant information to the log file. This includes but not limited to:
- Details of each stripper block
- Relevant KV's of all entities targetted by the stripper block
- The actions done on these entities
If the script fails to apply a line of stripper, it will produce a _WARNING:_ which you can filter by in the log file. This can include any invalid stripper fixes (e.g. deleting a non-existent KV) or stripper fixes that the script cannot resolve.
If the script failes to apply the entie block of stripper, if will produce an **ERROR:**. These are fatal errors in which you should notify the creators with.
_Note, the script may fail to produce a WARNING when it should have - always check to make sure if the stripper has been applied correctly!_
## Notes
- The script will not check if all files present are valid and uncorrupted; double check if your stripper .cfg has no mistakes in it!
- The script will not work in all cases, especially if a stripper block uses somewhat niche techniques. Whenever applicable, an error or a warning is given so that these stripper fixes can be done manually
- The strippered .vmf may crash your hammer by an exception error - you can simply reopen the strippered .vmf
  - For this reason, you should save the strippered .vmf before doing any further modifications - hammer needs to assign id to any newly created entities
and most importantly,
- The script is still in development, so if you encounter any fatal errors or have a suggestion then you can comment about those here
