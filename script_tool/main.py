from src.Sogna import *
import argparse

def main():
    parser = argparse.ArgumentParser(description='Process some .Win files.')
    parser.add_argument('-u', action='store_true', help='Invoke function to extract text from .win files')
    parser.add_argument('-r', action='store_true', help='Invoke function to replace text in script and get new files')
    parser.add_argument('-p', action='store_true', help='Invoke function to patch SGS.DAT to add new translated .win files.')
    args = parser.parse_args()

    sogna = Sogna()

    if not any(vars(args).values()):
        parser.print_help()
        sogna.__init__()

    else:
        if args.u:
            sogna.extract_win()
            sogna.fix_files()
        elif args.r:
            sogna.start_replace()
        elif args.p:
            sogna.get_details()
            print("Patching File...")
            sogna.patch()
            print("Patch Completed")

if __name__ == "__main__":
    main()
