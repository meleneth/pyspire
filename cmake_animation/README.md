01_simple_compile

This shows what happens when you run c++ main.cpp secondary_src.cpp -o some_program

g++ kicks the process off by compiling main.cpp
main.cpp starts compiling, sees a include for secondary.hpp, pauses, and compiles secondary.hpp
when secondary.hpp is finished, main.cpp resumes compiling
when main.cpp is finished, secondary.cpp starts compiling
secondary starts compiling, sees a include for secondary.hpp, pauses, and compiles secondary.hpp
when secondary.hpp is finished, secondary.cpp resumes compiling
when secondary.cpp is finished, the program some_program is written to disk

02_compile_with_objects
This shows what happens when you run

```
    g++ -Wall -Wextra -O2 -MMD -MP -c main.cpp -o main.o
    g++ -Wall -Wextra -O2 -MMD -MP -c secondary.cpp -o secondary.o
    g++ main.o secondary.o -o some_program
```

g++ kicks the process off by compiling main.cpp
main.cpp starts compiling, sees a include for secondary.hpp, pauses, and compiles secondary.hpp
when secondary.hpp is finished, main.cpp resumes compiling
when main.cpp is finished, it creates main.o, and secondary.cpp starts compiling
secondary starts compiling, sees a include for secondary.hpp, pauses, and compiles secondary.hpp
when secondary.hpp is finished, it creates secondary.o and secondary.cpp resumes compiling
when secondary.cpp is finished, g++ takes the two .o files and passes them to the linker
then the program some_program is written to disk
