a=float(input("a = "))
b=float(input("b = "))
c=float(input("c1 = "))

discr = b**2 - 4*a*c

print("Дискриминат = ", discr)

if a==0:
    print("Некорректный ввод")
elif discr > 0:
    x1=(-b+discr**0.5)/2*a
    x2=(-b-discr**0.5)/2*a
    print("Уравнение имеет 2 корня: ", x1, " и ", x2, ". D = ", discr)
elif discr == 0:
    x = (-b)/2*a
    print("Уравнение имеет 1 корень: ", x, ". D = ", discr)
else:
    x1=(-b+discr**0.5)/2*a
    x2=(-b-discr**0.5)/2*a
    print("Уравнение имеет 2 комплексных числа: ", x1, " и ", x2, ". D = ", discr)
