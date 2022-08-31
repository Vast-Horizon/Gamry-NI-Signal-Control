import GamrySignalImport
import NIProjectImport

def main():
    while True:
        try:
            print("\n=============================================================\n")
            num = int(input("Enter 1 to start National Instruments Module\nEnter 2 to start Gamry Signal Generator\n"))
            if num==1:
                NIProjectImport.mainfunc()
            elif num==2:
                GamrySignalImport.mainfunc()
        except ValueError as ve:
            print("Please try again. 1 or 2")

if __name__ == "__main__":
    main()
