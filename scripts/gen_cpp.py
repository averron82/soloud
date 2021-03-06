#!/usr/bin/env python3
""" SoLoud D wrapper generator """

import soloud_codegen

fo = open("../glue/soloud.hpp", "w")


C_TO_C_TYPES = {
    "string":"string",
    "int":"int",
    "void":"void",
    "const char *":"const char *",
    "char *":"char *",
    "unsigned int":"unsigned int",
    "float":"float",
    "double":"double",
    "float *":"float *",
    "File *":"SoloudObject *",
    "unsigned char *":"unsigned char *",
    "unsigned char":"unsigned char",
    "short *":"short *"
}

CROSS_OBJ = []

for soloud_type in soloud_codegen.soloud_type:
    C_TO_C_TYPES[soloud_type + " *"] = soloud_type + " *"
    CROSS_OBJ.append(soloud_type + " *")

def has_ex_variant(funcname):
    """ Checks if this function has an "Ex" variant """
    if funcname[-2::] == "Ex":
        # Already an Ex..
        return False
    for func in soloud_codegen.soloud_func:
        if func[1] == (funcname + "Ex"):
            return True
    return False

fo.write("""
// SoLoud wrapper for CPP
// This file is autogenerated; any changes will be overwritten

// This is a single-file library. Use SOLOUD_HPP_IMPLMENTATION
// in ONE source file before including this file.
// like:
// #define SOLOUD_HPP_IMPLMENTATION
// #include "soloud.hpp"

#ifndef SOLOUD_HPP_INCLUDED
#define SOLOUD_HPP_INCLUDED

namespace SoLoud
{

\tclass SoloudObject
\t{
\tpublic:
\t\tSoloudObject *mObjhandle;
\t};

""")

# Forward declare ALL THE CLASSES
for soloud_type in soloud_codegen.soloud_type:
    fo.write("\tclass %s;\n"%(soloud_type))


# Since there's no reason to use the "raw" data anymore,
# skip generating the enum dictionary
#
#fo.write("# Enumerations\n")
#fo.write("soloud_enum = {\n")
#first = True
#for x in soloud_codegen.soloud_enum:
#    if first:
#        first = False
#    else:
#        fo.write(",\n")
#    fo.write('"' + x + '": ' + str(soloud_codegen.soloud_enum[x]))
#fo.write("\n}\n")

fo.write("\n")
# fo.write("# Raw DLL functions\n")
# for x in soloud_codegen.soloud_func:
#     fo.write(x[1] + ' = soloud_dll.' + x[1] + '\n')
#     fo.write(x[1] + '.restype = ' + C_TO_C_TYPES[x[0]] + '\n')
#     fo.write(x[1] + '.argtypes = [')
#     first = True
#     for y in x[2]:
#         if len(y) > 0:
#             if first:
#                 first = False
#             else:
#                 fo.write(", ")
#             fo.write(fudge_types(y[0]))
#     fo.write(']\n')
#     fo.write('\n')
#
#################################################################
#
# oop
#

def fix_default_param(defparam, classname):
    """ 'fixes' default parameters from C to what python expectes """
    if (classname + '::') == defparam[0:len(classname)+2:]:
        return defparam[len(classname)+2::]
    #if defparam[len(defparam)-1] == "f":
    #    return defparam[0:len(defparam)-1]
    return defparam

def external_pointer_fix(param):
    if param == "SoloudObject":
        return "int *"
    return param


for x in soloud_codegen.soloud_type:
    first = True
    for y in soloud_codegen.soloud_func:
        if (x + "_") == y[1][0:len(x)+1:]:
            if first:
                fo.write('\n')
                fo.write('\tclass %s : public SoloudObject\n\t{\n'%(x))
                fo.write('\tpublic:\n')
                enums = ""
                for z in soloud_codegen.soloud_enum:
                    if z[0:len(x)+1] == x.upper()+'_':
                        s = str(soloud_codegen.soloud_enum[z])
                        enums += '\t\t\t%s = %s,\n'%(z[len(x)+1::], s)
                if len(enums)>1:
                    fo.write('\n\t\tenum\n\t\t{\n')
                    fo.write(enums)
                    fo.write('\t\t};\n\n')

                fo.write('\t\t%s();\n'%(x))
                fo.write('\t\t~%s();\n'%(x))

                first = False
            funcname = y[1][len(x)+1::]
            # If the function has the name "Ex", remove the subfix
            if funcname[-2::] == "Ex":
                funcname = funcname[:len(funcname)-2]
            # Skip generating functions that have an Ex variant
            if funcname == "create" or funcname == "destroy" or has_ex_variant(y[1]):
                pass
            else:
                ret = C_TO_C_TYPES[y[0]]

                fo.write('\t\t%s %s('%(C_TO_C_TYPES[y[0]], funcname))
                firstparm = True
                for z in y[2]:
                    if len(z) > 1:
                        if z[1] == 'a'+x:
                            pass # skip the 'self' pointer
                        else:
                            if firstparm:
                                firstparm = False
                            else:
                                fo.write(', ')
                            if len(z) > 2:
                                fo.write('\n\t\t\t')
                            fo.write(C_TO_C_TYPES[z[0]] + ' ' + z[1])
                            if len(z) > 2:
                                fo.write(' = ' + fix_default_param(z[2], x))
                fo.write(');\n')
    if not first:
        fo.write('\t};\n')

#fo.write(function_decls)

fo.write("""

////////////////////////////////////

#ifdef SOLOUD_HPP_IMPLEMENTATION

\tnamespace dll
\t{
""")

# dll imports

for x in soloud_codegen.soloud_func:
    fo.write('\t\ttypedef %s (*%s_func)('%(C_TO_C_TYPES[x[0]], x[1]))
    first = True
    for y in x[2]:
        if len(y) > 0:
            if first:
                first = False
            else:
                fo.write(", ")
            fo.write(C_TO_C_TYPES[y[0]])
    fo.write(');\n')
    fo.write('\t\tstatic %s_func %s = 0;\n'%(x[1],x[1]))

fo.write("""
#ifdef _WIN32
#include <windows.h>

\t\tstatic HMODULE open_dll()
\t\t{
\t\t\tHMODULE res = LoadLibraryA("soloud_x86.dll");
\t\t\tif (!res) res = LoadLibraryA("soloud_x64.dll");
\t\t\tif (!res) res = LoadLibraryA("soloud.dll");
\t\t\treturn res;
\t\t}

\t\tstatic void* get_dll_proc(HMODULE aDllHandle, const char *aProcName)
\t\t{
\t\t\treturn GetProcAddress(aDllHandle, aProcName);
\t\t}

#else
#include <dlfcn.h> // dll functions

\t\tstatic void * open_dll()
\t\t{
\t\t\tvoid * res;
\t\t\tres = dlopen("soloud_x86.so", RTLD_LAZY);
\t\t\tif (!res) res = dlopen("soloud_x64.so", RTLD_LAZY);
\t\t\tif (!res) res = dlopen("soloud.so", RTLD_LAZY);
\t\t\treturn res;
\t\t}

\t\tstatic void* get_dll_proc(void * aLibrary, const char *aProcName)
\t\t{
\t\t\treturn dlsym(aLibrary, aProcName);
\t\t}

#endif

\t\tvoid init_dll()
\t\t{
\t\t\tif (Soloud_create) return;
#ifdef _WIN32
\t\t\tHMODULE dll = NULL;
#else
\t\t\tvoid * dll = NULL;
#endif
\t\t\tdll = open_dll();
""")

for x in soloud_codegen.soloud_func:
    fo.write('\t\t\t%s = (%s_func)get_dll_proc(dll, "%s");\n'%(x[1],x[1],x[1]))
    
 
fo.write("""
\t\t}

\t}; // namespace dll

""")

# glue func implementation

for x in soloud_codegen.soloud_type:
    fo.write('\t%s::%s()\n\t{\n'%(x,x))
    fo.write('\t\tdll::init_dll();\n')
    fo.write('\t\tmObjhandle = dll::%s_create();\n'%(x))
    fo.write('\t}\n\n')
    fo.write('\t%s::~%s()\n\t{\n'%(x,x))
    fo.write('\t\tdll::%s_destroy((%s *)mObjhandle);\n'%(x,x))
    fo.write('\t}\n\n')
    for y in soloud_codegen.soloud_func:
        if (x + "_") == y[1][0:len(x)+1:]:
            funcname = y[1][len(x)+1::]
            # If the function has the name "Ex", remove the subfix
            if funcname[-2::] == "Ex":
                funcname = funcname[:len(funcname)-2]
            # Skip generating functions that have an Ex variant
            if funcname == "create" or funcname == "destroy" or has_ex_variant(y[1]):
                pass
            else:
                ret = C_TO_C_TYPES[y[0]]

                fo.write('\t%s %s::%s('%(C_TO_C_TYPES[y[0]], x, funcname))
                firstparm = True
                for z in y[2]:
                    if len(z) > 1:
                        if z[1] == 'a'+x:
                            pass # skip the 'self' pointer
                        else:
                            if firstparm:
                                firstparm = False
                            else:
                                fo.write(', ')
                            fo.write(C_TO_C_TYPES[z[0]] + ' ' + z[1])
                fo.write(')\n\t{\n')
                fo.write('\t\t')
                if y[0] == 'void':
                    pass
                else:
                    fo.write('return ')
                fo.write('dll::' + y[1] + '((Soloud *)mObjhandle')
                for z in y[2]:
                    if len(z) > 1:
                        if z[1] == 'a'+x:
                            pass # skip the 'self' pointer
                        else:
                            fo.write(', ')
                            if z[0] in CROSS_OBJ:
                                fo.write('(%s)((SoloudObject *)%s)->mObjhandle'%(z[0],z[1]))
                            else:
                                fo.write(z[1])
                fo.write(');\n')
                fo.write('\t}\n\n')

fo.write("""
#endif //SOLOUD_HPP_IMPLEMENTATION

}; // namespace SoLoud

#endif //SOLOUD_HPP_INCLUDED
""")

fo.close()

print("soloud.hpp generated")
