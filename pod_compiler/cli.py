"""
Command Line Interface for Pod Compiler

Usage:
    python -m pod_compiler.cli compile --theatre T1042 --rating PG-13 \
        --section LPS --aspect Flat --start-date 06-Feb-2026 \
        --cpls ad1.xml ad2.xml ad3.xml ad4.xml
"""

import argparse
import sys
from pathlib import Path

from .compiler import PodCompiler, PodCompilerError
from .pod_identity import PodIdentity


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='SVN-Symphony Ad Pod Compiler',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compile a pod with 4 ads
  python -m pod_compiler.cli compile \\
    --theatre T1042 \\
    --rating PG-13 \\
    --section LPS \\
    --aspect Flat \\
    --start-date 06-Feb-2026 \\
    --cpls ad1.xml ad2.xml ad3.xml ad4.xml
  
  # Specify output directory and asset repository
  python -m pod_compiler.cli compile \\
    --theatre T1042 \\
    --rating PG-13 \\
    --section LPS \\
    --aspect Flat \\
    --start-date 06-Feb-2026 \\
    --cpls ad1.xml ad2.xml ad3.xml ad4.xml \\
    --output ./pods \\
    --assets ./asset_repo
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Compile command
    compile_parser = subparsers.add_parser('compile', help='Compile an ad pod')
    compile_parser.add_argument(
        '--theatre',
        required=True,
        help='Theatre ID (e.g., T1042)'
    )
    compile_parser.add_argument(
        '--rating',
        required=True,
        choices=['G', 'PG', 'PG-13', 'R'],
        help='Content rating'
    )
    compile_parser.add_argument(
        '--section',
        required=True,
        choices=['LPS', 'EPS'],
        help='Section (LPS or EPS)'
    )
    compile_parser.add_argument(
        '--aspect',
        required=True,
        choices=['Flat', 'Scope'],
        help='Aspect ratio (Flat or Scope)'
    )
    compile_parser.add_argument(
        '--start-date',
        required=True,
        help='Start date in dd-mmm-yyyy format (e.g., 06-Feb-2026)'
    )
    compile_parser.add_argument(
        '--cpls',
        nargs='+',
        required=True,
        help='Ordered list of CPL XML files (up to 20)'
    )
    compile_parser.add_argument(
        '--output',
        default='./output',
        help='Output directory (default: ./output)'
    )
    compile_parser.add_argument(
        '--assets',
        help='Path to asset repository (optional)'
    )
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate date format')
    validate_parser.add_argument(
        'date',
        help='Date to validate in dd-mmm-yyyy format'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == 'compile':
        return compile_command(args)
    elif args.command == 'validate':
        return validate_command(args)
    
    return 0


def compile_command(args):
    """Execute compile command"""
    print("=" * 70)
    print("SVN-Symphony Ad Pod Compiler")
    print("=" * 70)
    
    # Validate date format
    if not PodIdentity.validate_date_format(args.start_date):
        print(f"\n❌ Error: Invalid date format '{args.start_date}'")
        print("   Expected format: dd-mmm-yyyy (e.g., 06-Feb-2026)")
        return 1
    
    # Validate CPL files exist
    missing_files = []
    for cpl_file in args.cpls:
        if not Path(cpl_file).exists():
            missing_files.append(cpl_file)
    
    if missing_files:
        print("\n❌ Error: CPL files not found:")
        for f in missing_files:
            print(f"   - {f}")
        return 1
    
    # Check CPL count
    if len(args.cpls) > 20:
        print(f"\n❌ Error: Too many CPL files ({len(args.cpls)}). Maximum is 20.")
        return 1
    
    print(f"\nTheatre:     {args.theatre}")
    print(f"Rating:      {args.rating}")
    print(f"Section:     {args.section}")
    print(f"Aspect:      {args.aspect}")
    print(f"Start Date:  {args.start_date}")
    print(f"CPL Files:   {len(args.cpls)}")
    print(f"Output Dir:  {args.output}")
    if args.assets:
        print(f"Assets:      {args.assets}")
    print()
    
    # Compile pod
    try:
        compiler = PodCompiler(asset_repository=args.assets)
        result = compiler.compile_pod(
            theatre_id=args.theatre,
            rating=args.rating,
            section=args.section,
            aspect=args.aspect,
            start_date=args.start_date,
            cpl_files=args.cpls,
            output_dir=args.output
        )
        
        print(f"\n✅ SUCCESS: Pod compiled successfully!")
        print(f"\nOutput directory: {result['output_dir']}")
        
        return 0
        
    except PodCompilerError as e:
        print(f"\n❌ COMPILATION FAILED:")
        print(f"   {e}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR:")
        print(f"   {e}")
        import traceback
        traceback.print_exc()
        return 1


def validate_command(args):
    """Execute validate command"""
    if PodIdentity.validate_date_format(args.date):
        print(f"✅ Valid date format: {args.date}")
        parsed = PodIdentity.parse_date(args.date)
        print(f"   Parsed as: {parsed.strftime('%A, %B %d, %Y')}")
        return 0
    else:
        print(f"❌ Invalid date format: {args.date}")
        print("   Expected format: dd-mmm-yyyy (e.g., 06-Feb-2026)")
        return 1


if __name__ == '__main__':
    sys.exit(main())
