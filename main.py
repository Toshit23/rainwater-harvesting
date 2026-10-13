"""
main.py - Rainwater Harvesting Potential Estimator

Custom Image & Site Processing:
  1. Select your drone / aerial image (browse via file dialog or enter path)
  2. Enter site location & physical area
  3. Enter construction parameters
  4. Automatically runs OpenCV building detection on YOUR image,
     fetches historical rainfall from Open-Meteo, and computes the water balance.

Usage:
  python main.py
"""

import sys
import os

# Ensure local packages can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api import get_rainfall_for_location
from calculations import calculate_project_result
from area_detection import detect_building_area_percentage


def choose_image_path() -> str:
    """Prompt the user for an image path or open a file browser dialog."""
    print("  1. Select Aerial / Drone Image:")
    print("     -> Type/paste file path (or press Enter to open File Explorer dialog):")
    user_input = input("     Image path: ").strip().strip('\"\'')

    if user_input and os.path.isfile(user_input):
        return user_input

    # If user pressed enter or input path was not found, open Windows File Dialog
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected_file = filedialog.askopenfilename(
            title="Select Site Drone / Aerial Image",
            filetypes=[("Image files", "*.jpg;*.jpeg;*.png;*.bmp;*.webp"), ("All files", "*.*")]
        )
        root.destroy()
        if selected_file and os.path.isfile(selected_file):
            print(f"     -> Selected file: {selected_file}")
            return selected_file
    except Exception:
        pass

    # If still not found, prompt again until valid
    while True:
        if user_input and not os.path.isfile(user_input):
            print(f"     [!] File not found: '{user_input}'")
        user_input = input("     Please enter a valid image file path: ").strip().strip('\"\'')
        if os.path.isfile(user_input):
            return user_input


def prompt_number(prompt_text: str, default_val: float) -> float:
    """Prompt for a number with a default fallback."""
    val_str = input(f"{prompt_text} [{default_val}]: ").strip()
    if not val_str:
        return default_val
    try:
        return float(val_str.replace(",", ""))
    except ValueError:
        print(f"     -> Invalid input. Using default: {default_val}")
        return default_val


def main():
    print("=" * 75)
    print("      RAINWATER HARVESTING & CONSTRUCTION WATER ESTIMATOR")
    print("=" * 75)
    print("Enter your project inputs below:\n")

    # 1. Image Selection
    image_path = choose_image_path()

    # 2. Site Address
    while True:
        address = input("\n  2. Site Location / City (e.g. Powai, Mumbai): ").strip()
        if address:
            break
        print("     -> City/Location cannot be empty.")

    # 3. Total Physical Site Area
    while True:
        area_str = input("  3. Total Physical Site Area in m² (e.g. 10000): ").strip()
        try:
            image_area_m2 = float(area_str.replace(",", ""))
            if image_area_m2 > 0:
                break
            print("     -> Area must be greater than 0.")
        except ValueError:
            print("     -> Please enter a valid number (e.g. 10000).")

    # 4. Construction Parameters
    print("\n  4. Construction Parameters (press Enter for standard defaults):")
    runoff_coeff = prompt_number("     - Runoff Coefficient          ", 0.80)
    concrete_m3  = prompt_number("     - Concrete Volume (in m³)     ", 100.0)
    plaster_m3   = prompt_number("     - Plaster Volume (in m³)      ", 50.0)
    curing_days  = prompt_number("     - Curing Duration (in days)   ", 14.0)

    # ---------------------------------------------------------
    # Processing Pipeline
    # ---------------------------------------------------------
    print("\n" + "=" * 75)
    print("  PROCESSING PIPELINE:")
    print("=" * 75)

    # Step A: OpenCV Detection on YOUR image
    print(f"  [1/3] Scanning '{os.path.basename(image_path)}' with OpenCV edge detection...")
    cv_info = detect_building_area_percentage(image_path)
    rooftop_pct = cv_info["rooftop_percentage"]
    print(f"        -> Detected: {cv_info['building_count']} building rooftops")
    print(f"        -> Measured Rooftop Coverage: {rooftop_pct:.2f}% of image area")
    print(f"        -> Annotated image saved to: {cv_info['annotated_image_path']}")

    # Step B: Weather API Lookup
    print(f"\n  [2/3] Fetching historical rainfall for '{address}' from Open-Meteo...")
    try:
        weather_res = get_rainfall_for_location(address, "2024-01-01", "2024-12-31")
        resolved_name = weather_res["location_name"]
        rainfall_mm = weather_res["total_rainfall_mm"]
        print(f"        -> Resolved: {resolved_name}")
        print(f"        -> Annual Rainfall: {rainfall_mm:,.1f} mm")
    except Exception as err:
        print(f"        -> Weather API error ({err}). Using fallback 2,200 mm.")
        resolved_name = address
        rainfall_mm = 2200.0

    # Step C: Civil Engineering Calculations
    print("\n  [3/3] Performing rainwater harvesting and water demand calculations...")
    result = calculate_project_result(
        image_area_m2=image_area_m2,
        rooftop_percentage=rooftop_pct,
        rainfall_mm=rainfall_mm,
        runoff_coefficient=runoff_coeff,
        concrete_volume_m3=concrete_m3,
        plaster_volume_m3=plaster_m3,
        curing_days=curing_days,
    )

    demand = result["demand_breakdown"]

    # ---------------------------------------------------------
    # Final Output Report
    # ---------------------------------------------------------
    print("\n" + "=" * 75)
    print("                           FINAL RESULTS")
    print("=" * 75)
    print(f"  Analyzed Image:           {os.path.abspath(image_path)}")
    print(f"  Site Location:            {resolved_name}")
    print(f"  Total Site Physical Area: {result['image_area_m2']:>14,.2f} m²")
    print(f"  OpenCV Detected Rooftop %:{result['rooftop_percentage']:>14.2f} % ({cv_info['building_count']} buildings)")
    print(f"  Calculated Rooftop Area:  {result['rooftop_area_m2']:>14,.2f} m²")
    print(f"  Annual Rainfall:          {result['rainfall_mm']:>14,.1f} mm")
    print(f"  Runoff Coefficient:       {result['runoff_coefficient']:>14.2f}")

    print("\n" + "-" * 75)
    print("  1. WATER SUPPLY (RAINWATER HARVESTING POTENTIAL)")
    print("-" * 75)
    print(f"  Formula: Area ({result['rooftop_area_m2']:,.1f} m²) × Rainfall ({result['rainfall_mm']:.1f} mm) × Coeff ({result['runoff_coefficient']:.2f})")
    print(f"  Total Harvestable Water:  {result['harvested_water_litres']:>14,.0f} Litres")
    print(f"                            {result['harvested_water_kl']:>14,.2f} kL")

    print("\n" + "-" * 75)
    print("  2. WATER DEMAND (CONSTRUCTION ACTIVITIES)")
    print("-" * 75)
    print(f"  - Concrete Production:    {demand['concrete_water_litres']:>14,.0f} L ({concrete_m3:.0f} m³ × 180 L/m³)")
    print(f"  - Plastering Works:       {demand['plaster_water_litres']:>14,.0f} L ({plaster_m3:.0f} m³ × 160 L/m³)")
    print(f"  - Curing Allowance:       {demand['curing_water_litres']:>14,.0f} L ({curing_days:.0f} days)")
    print(f"  Total Construction Demand:{result['construction_water_demand_litres']:>14,.0f} Litres")
    print(f"                            {result['construction_water_demand_kl']:>14,.2f} kL")

    print("\n" + "-" * 75)
    print("  3. WATER BALANCE & STATUS")
    print("-" * 75)
    print(f"  Overall Status:           {result['status']}")
    if result["status"] == "SURPLUS":
        print(f"  Net Water Surplus:       +{result['surplus_litres']:>14,.0f} Litres (+{result['surplus_litres']/1000:,.2f} kL)")
        print("  -> Conclusion: Harvested rainwater is SUFFICIENT to fulfill site construction needs!")
    elif result["status"] == "SHORTFALL":
        print(f"  Net Water Shortfall:     -{result['shortfall_litres']:>14,.0f} Litres (-{result['shortfall_litres']/1000:,.2f} kL)")
        print("  -> Conclusion: Additional external water source required.")
    else:
        print("  Supply and demand are exactly balanced.")
    print("=" * 75)
    print(f"\nAnnotated detection saved at: {os.path.abspath(cv_info['annotated_image_path'])}\n")


if __name__ == "__main__":
    main()
