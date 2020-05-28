# Fortiori
A proof of concept for adding syntactic sugar to FORTRAN. The goal of _fortiori_
is to provide a friendlier syntax for FORTRAN afficionados while still producing
mostly-compliant FORTRAN code which can then be compiled normally using
gfortran and the like.

## Supported Features
- [x] Declaration of function return types in caller
- [x] Case-sensitive identifiers
- [x] Automatically add 'implicit none'
- [x] Return statement with value
- [ ] Import/multi-file support
- [ ] Convert void functions to subroutines
- [x] If-else conditional blocks
- [x] Do loops with inline variable declaration

## Example (WIP)
```fortran
integer function getFirstPrime(integer::lower, integer::higher) {
    return 5;
}

program {
    print*, "Getting a prime...";
    integer::Prime = getFirstPrime(1,10);
    integer::PRIME = 10;
    if (PRIME == 10) {
    print*, "condition is true";
    } else {
    print*, "condition is false";
    }

    do integer::n = 1,10 {
    print*, n;
    }
    do while ( n < 15) {
       print*, n, "incrementing...";
       n = n+1;
    }

    print*, "This is a prime:", Prime;
    print*, "This is another prime:", PRIME;
}
```

This would yield the following FORTRAN code
```fortran
integer function getf$irstp$rime(lower,higher) 
implicit none;
integer::lower
integer::higher
 getf$irstp$rime = 5;
return;
end function;
program main 
implicit none;
integer::getf$irstp$rime;
integer::p$rime;
integer::p$$rime$$;
 integer::n;
print*, "Getting a prime...";
p$rime = getf$irstp$rime(1,10);
p$$rime$$ = 10;
 if (p$$rime$$ == 10) then
 print*, "condition is true";
 else
 print*, "condition is false";
 end if;
do n = 1,10 
 print*, n;
 
end do;
 do while ( n < 15) 
 print*, n, "incrementing...";
 n = n+1;
 
end do;
 print*, "This is a prime:", p$rime;
 print*, "This is another prime:", p$$rime$$;
end program;⏎ 
```

