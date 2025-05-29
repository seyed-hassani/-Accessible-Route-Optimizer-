#!/usr/bin/env python3
"""
Accessible Route Optimizer - Main Entry Point
Command-line interface for finding accessible transit routes
"""

import argparse
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent))

from routing_engine import AccessibleRouter
from data_loader import DataLoader


def main():
    parser = argparse.ArgumentParser(
        description="Find accessible public transit routes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --start "Union Station" --end "Yorkdale"
  python main.py --start "Dundas" --end "Bloor" --accessible-only
  python main.py --start "King" --end "Queen" --avoid-stairs --wheelchair
        """
    )
    
    # Required arguments
    parser.add_argument("--start", "-s", required=True,
                       help="Starting station/stop name")
    parser.add_argument("--end", "-e", required=True,
                       help="Destination station/stop name")
    
    # Accessibility options
    parser.add_argument("--accessible-only", action="store_true",
                       help="Only use wheelchair accessible routes")
    parser.add_argument("--wheelchair", action="store_true",
                       help="Require wheelchair accessible vehicles")
    parser.add_argument("--avoid-stairs", action="store_true",
                       help="Avoid routes with stairs")
    parser.add_argument("--elevator-required", action="store_true",
                       help="Only use routes with working elevators")
    
    # Data options
    parser.add_argument("--transit-data", default="data/sample_transit.csv",
                       help="Path to transit network CSV file")
    parser.add_argument("--accessibility-data", default="data/accessibility.json",
                       help="Path to accessibility metadata JSON file")
    
    # Output options
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Show detailed route information")
    parser.add_argument("--json", action="store_true",
                       help="Output results in JSON format")
    
    args = parser.parse_args()
    
    try:
        # Load data
        print("Loading transit network data...")
        data_loader = DataLoader()
        transit_graph = data_loader.load_transit_csv(args.transit_data)
        accessibility_data = data_loader.load_accessibility_json(args.accessibility_data)
        
        # Initialize router
        router = AccessibleRouter(transit_graph, accessibility_data)
        
        # Build accessibility requirements
        requirements = []
        if args.accessible_only or args.wheelchair:
            requirements.append('wheelchair_accessible')
        if args.avoid_stairs:
            requirements.append('no_stairs')
        if args.elevator_required:
            requirements.append('working_elevator')
        
        print(f"\nFinding route from '{args.start}' to '{args.end}'...")
        if requirements:
            print(f"Accessibility requirements: {', '.join(requirements)}")
        
        # Find the route
        if requirements:
            result = router.find_accessible_path(args.start, args.end, requirements)
        else:
            result = router.find_path(args.start, args.end)
        
        # Display results
        if result['path']:
            if args.json:
                import json
                print(json.dumps(result, indent=2))
            else:
                print(f"\n✅ Route found!")
                print(f"Path: {' → '.join(result['path'])}")
                print(f"Total time: {result['total_time']} minutes")
                print(f"Transfers: {result['transfers']}")
                
                if args.verbose and 'details' in result:
                    print("\nDetailed route information:")
                    for i, segment in enumerate(result['details']):
                        print(f"  {i+1}. {segment['from']} → {segment['to']}")
                        print(f"     Route: {segment['route']} ({segment['time']} min)")
                        if segment.get('accessibility_notes'):
                            print(f"     ♿ {segment['accessibility_notes']}")
        else:
            print(f"\n❌ No accessible route found between '{args.start}' and '{args.end}'")
            if result.get('message'):
                print(f"Reason: {result['message']}")
            
            # Suggest alternatives
            if not requirements:
                print("\nTry using --accessible-only for accessibility-focused routing")
    
    except FileNotFoundError as e:
        print(f"❌ Error: Data file not found - {e}")
        sys.exit(1)
    except KeyError as e:
        print(f"❌ Error: Station not found - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
