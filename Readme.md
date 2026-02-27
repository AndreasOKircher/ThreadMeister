<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows%20✔-0078D6?style=for-the-badge" alt="Windows Tested">
  <img src="https://img.shields.io/badge/Platform-macOS%20⚠%20Pending-999999?style=for-the-badge" alt="macOS Pending">
  <img src="https://img.shields.io/badge/Fusion%20360-Add--In-FF6F00?style=for-the-badge" alt="Fusion 360 Add-In">
  <img src="https://img.shields.io/badge/Language-Python-3776AB?style=for-the-badge" alt="Python">
  <img src="https://img.shields.io/badge/License-GPL--3.0--or--later-blue?style=for-the-badge" alt="GPL-3.0-or-later">
  <img src="https://img.shields.io/badge/Distribution-GitHub%20%7C%20App%20Store-6E40C9?style=for-the-badge" alt="Distribution">
</p>

<div align="center">
  <img src="resources/images/Title.png" alt="ThreadMeister Logo" width="600">
</div>

# ThreadMeister – Heat-Set Insert Add-in for Fusion 360
An add-in for Autodesk Fusion 360 that automates the creation of heat-set insert holes for 3D printing, using insert dimension recommendations from [CNC Kitchen](https://cnckitchen.com).

## Features

-  **Pre-configured insert sizes** - CNC Kitchen’s recommended dimensions for common sizes (M2, M2.5, M3, M4, M5, M6, M8, M10, and 1/4"-20 camera thread)
-  **Blind holes and through holes** - Automatically calculates correct depths
- Automatic **top chamfer** (0.5 mm × 45°; fully customizable)
- Automatic **bottom fillet** (0.5 mm radius; fully customizable)
-  **Multiple holes at once** - Select multiple sketch points to create several holes in one operation
-  **Timeline grouping** - All operations grouped with descriptive names for easy management
-  **Direct integration** - Holes are cut directly into your part, no manual combine operations needed
-  **User-friendly interface** - Button in SOLID > MODIFY menu with intuitive dialog

## Platform Support

- **Windows**: Fully tested  
- **macOS**: Expected to work; not yet fully verified due to lack of hardware  
  - Code uses cross‑platform paths (`os.path.join`)  
  - No Windows‑specific APIs  
  - Icon loading and geometry creation should behave identically  


## Installation

### Method 1: Manual Installation

1. Download this repository (Code → Download ZIP)
2. Extract the `ThreadMeister` folder
3. Copy the folder to your Fusion 360 Add-Ins directory:
   - **Windows**: `C:\Users\[YourUsername]\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\`
   - **macOS**: `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/`
4. Restart Fusion 360
5. Go to **Utilities** → **Add-Ins** → **Scripts and Add-Ins** → **Add-Ins** tab
6. Find `ThreadMeister` and click **Run**
7. Optional: Check **Run on Startup** to load automatically

### Autodesk App Store Installation
ThreadMeister is also available on the Autodesk App Store (pending approval).  
The App Store version installs automatically and updates cleanly.


### Method 2: Git Clone

```bash
cd "C:\Users\[YourUsername]\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\"
git clone git clone https://github.com/AndreasOKircher/ThreadMeister.git ThreadMeister
```

## Usage

### Quick Start

1. **Create a sketch** and place **sketch points** or use existing line/arc endpoints where insert holes should be created.  
2. **Finish the sketch**  
3. Click the **"ThreadMeister"** button in **SOLID → MODIFY** menu
4. **Select your target body** (the part to add holes to)
5. **Select one or more sketch points**  
6. Choose your **insert size** (e.g., M3 x 5.7mm standard)
7. Choose **Blind Hole** or **Through Hole**
8. Enable/disable top **chamfer** and bottom **fillet** (recommended: enabled)
9. Click **OK**

### Insert Specifications

All dimensions follow CNC Kitchen's official recommendations:

| Insert Size | Hole Diameter | Insert Length | Min Wall Thickness |
|------------|---------------|---------------|-------------------|
| M2 x 3mm | 3.2mm | 3.0mm | 1.5mm |
| M2.5 x 4mm | 4.0mm | 4.0mm | 1.5mm |
| M3 x 3mm (short) | 4.4mm | 3.0mm | 1.6mm |
| M3 x 4mm (short) | 4.4mm | 4.0mm | 1.6mm |
| M3 x 5.7mm (standard) | 4.4mm | 5.7mm | 1.6mm |
| M4 x 4mm (short) | 5.6mm | 4.0mm | 2.0mm |
| M4 x 8.1mm (standard) | 5.6mm | 8.1mm | 2.0mm |
| M5 x 5.8mm (short) | 6.4mm | 5.8mm | 2.5mm |
| M5 x 9.5mm (standard) | 6.4mm | 9.5mm | 2.5mm |
| M6 x 12.7mm | 8.0mm | 12.7mm | 3.0mm |
| M8 x 12.7mm | 9.7mm | 12.7mm | 4.0mm |
| M10 x 12.7mm | 12.0mm | 12.7mm | 5.0mm |
| 1/4"-20 x 12.7mm | 8.0mm | 12.7mm | 3.0mm |

**Note:**  For blind holes, the add‑in automatically adds 1 mm extra depth for clearance by default.

### Customize settings
In the config.ini file you can:
-  Add your custom inserts. 
-  Set fillet and chamfer dimensions.
-  Set blind hole extra depth



## Screenshots

<div align="center"> <img src="resources/images/Screenshot1.png" alt="Located in the Modify Menu"> <br>
 <strong>Easy configure hole according insert spec</strong> 

 <br><br> <!-- spacing between images -->

 </div> <div align="center"> <img src="resources/images/Screenshot3.png" alt="Creates entry into the timeline"> <br>
  <strong>Bore is associated with sketch dimensions</strong> </div>


## Requirements

- Autodesk Fusion 360
- Python support (built into Fusion 360)
- Windows or macOS

## Tips

- **Print orientation matters**: Test hole sizes for your specific printer and orientation
- **Wall thickness**: Always ensure adequate wall thickness around holes
- **Multiple holes**: Select multiple points to create several holes efficiently
- **Timeline**: All operations are grouped - you can easily undo or suppress the entire set

## Troubleshooting

**Button doesn't appear:**
- Make sure the add-in is in the AddIns folder (not Scripts folder)
- Restart Fusion 360
- Check that the add-in is running in the Add-Ins tab

**Inserts or holes are the wrong size:**
- Add your own insert specifications to the config file (or change existing definitions)

**Chamfer or fillet radius missing:**
- The chamfer and fillet radius can be selected in the config menu


## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Credits

- **Developed by**: [Andreas Kircher](https://github.com/AndreasOKircher)
- **Code assistance**: CAI‑assisted coding using Perplexity / Claude
- **Insert specifications**: [CNC Kitchen](https://cnckitchen.com)


## License

This project is licensed under the GNU General Public License v3.0 (GPL‑3.0).
See the LICENSE file for details.

## Disclaimer

This add-in is not affiliated with or endorsed by CNC Kitchen or Autodesk. All insert specifications are publicly available from CNC Kitchen's documentation. Use at your own risk and always verify dimensions for your specific application.

## Support

If you find this add-in useful, consider:
- ⭐ Starring this repository
- 🐛 Reporting issues or suggesting improvements
- 🛒 Supporting [CNC Kitchen](https://cnckitchen.store) by purchasing their high-quality inserts

---

## Known Technical Limitations

### Through‑hole extrusion instability
Fusion 360 may fail to create through‑hole extrusions in certain situations. This typically occurs when the sketch or target body contains complex or ambiguous geometry that prevents Fusion from resolving a clean cut.

Symptoms include:
- Missing through‑hole cut  
- Partial cut that stops before exiting the body  
- “Profile not found” or “Operation failed” errors  

Common causes:
- Complex or thin‑walled bodies  
- Ambiguous extrusion direction  
- Overlapping or poorly defined profiles  

Workarounds:
- Simplify the geometry around the bore location  
- Ensure the target body has clean, manifold geometry  
- Move the bore point into a separate sketch  

---

### Sketch profile overload near the bore circle
Fusion 360 may fail to create the bore, chamfer, or fillet if the sketch contains too many intersecting lines around the selected sketch point. When ThreadMeister creates the inner bore circle, Fusion automatically detects all enclosed regions (profiles). If this area contains more than ~15 profiles, operations may fail.

Symptoms include:
- Bore not extruded as a clean cylinder  
- Chamfer operation fails  
- Fillet operation fails  
- “Profile not found” or “Operation failed”  

Common causes:
- Dense or complex sketches  
- Many crossing lines near the bore location  
- Imported DXF geometry  
- Leftover construction lines or unused sketch elements  
- Parametric sketches with heavy constraints  

Workarounds:
- Simplify the sketch around the bore location  
- Isolate the bore circle on a separate sketch  
- Remove or convert unnecessary lines to construction geometry  
- Avoid overlapping sketch elements in the bore region  





**Happy 3D printing!** 🎉