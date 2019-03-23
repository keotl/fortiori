integer function get_first_prime(lower, higher)
    integer :: lower, higher
    get_first_prime = 5
end function get_first_prime

program myProgram
    implicit none;
    integer :: a_prime
    integer :: get_first_prime;

    a_prime = get_first_prime(1, 10)

    print*, "This is a prime:", a_prime

end program myProgram
