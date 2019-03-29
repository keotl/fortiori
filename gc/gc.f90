module gc
  type, public:: Object
  end type Object

  type, public:: Reference
     integer,pointer:: ptr
  end type Reference

contains
  type(Reference) function gc_allocate(clazz)
    class(*),pointer:: clazz;
  end function
end module





program test_gc
  use gc;
  implicit none;
  type, extends(Object) :: MyObject
     integer, dimension(3)::content;
  end type MyObject

  class(Object),pointer :: genPointer;
  type(MyObject),target::concreteInstance = MyObject(3);
  type(MyObject),pointer:: downcastedInstance;

  genPointer => concreteInstance;

  print*, "Generic pointer: ", "loc:", loc(genPointer);
  print*, "Concrete Instance: ", concreteInstance, "loc:", loc(concreteInstance);

  select type (a => genPointer) ! automatically finds the most specific. type(MyObject) is more specific than class(MyObject)
  class is (MyObject)
     print*, "class is MyObject", a%content
  type is (Object)
     print*, "type is Object"
  type is (MyObject)
     print*, "type is MyObject", a%content
  class is (Object)
     print*, "class is Object"
  end select

  ! downcastedInstance = CAST(genPointer)
  select type(a => genPointer)
  class is (MyObject)
     downcastedInstance => a
  end select

  downcastedInstance%content(2) = 99;

  print*, "Generic pointer: ", "loc:", loc(genPointer);
  print*, "Concrete Instance: ", concreteInstance, "loc:", loc(concreteInstance);



end program test_gc

