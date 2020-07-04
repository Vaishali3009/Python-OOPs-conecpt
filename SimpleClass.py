
from random import randint
from datetime import date
import json


class Person():
    def __init__(self,name='',address='',phone='',dob=''):
        self.name=name
        self._address=address
        self._phone=phone
        self.dob=dob

     #Setter and getter for Address
    @property
    def address(self):
        return self._address

    @address.setter
    def address(self,value):
        self._address=value 


    #Setter and getter for Phone no
    @property
    def phone(self):
        return self._phone

    @phone.setter
    def phone(self,value):
        self._phone=value              

       

    def __str__(self):
        return f'\t\t\t\tPERSONAL INFORMATION-\n\n Name: {self.name}\t\t Address: {self.address}\t\t DOB: {self.address}\t\t Phoneno: {self.phone}'


class Employee(Person):
    def __init__(self,name='',address='',phone='',dob='',Ecode='',basic_salary=0.0,division=''):
        Person.__init__(self,name,address,phone,dob)
        self.Ecode=Ecode
      
        self.basic_salary=basic_salary
        self._division=division

     

    def input(self):
        self.name=input('Enter the Name:')
        self.address=input('Enter the Address: ')
        self.phone=input('Enter the Phone No: ')
        self.dob=input('Enter the DOB : ')
        self.basic_salary=int(input('Enter the Basic Salary : '))
        print('Choose the division:\n 1. Marketing\n 2. Sales\n 3. R&D\n 4. Admin ')
        div=input('Enter the division')
        if(div=='Marketing'):
            self._division='MK'
        elif(div=='Sales'):
            self._division='SL'
        elif(div=='R&D'):
            self._division='RD' 
        elif(div=='Admin'):
            self._division='ADM'
        else:
            print('Invalid option selected') 
         
        self.Ecode=self._division + str(randint(1000,9999))
    @property
    def division(self):
        return self._division

    @division.setter
    def division(self,value):
        self._division=value    


    def __str__(self):
        return f'{Person.__str__(self)}\n\t\t\t\t\n\n\nOFFICE DETAILS:\n\n Empno:{self.Ecode}\t\t\t Division: {self._division}'        

    


class Tax(Employee):
    def __init__(self,name='',address='',phone='',dob='',Ecode='',hra=0.0,da=0.0,ta=0.0,grosssalary=0.0,basic_salary=0.0,division=''):
        super().__init__(name,address,phone,dob,Ecode,basic_salary,division)
        self.hra=hra
        self.grosssalary=grosssalary
        self.ta=ta
        self.da=da
        

    def calculate_allowance(self):
        print(self.division)
        if(self.division=='MK'):
        
            self.hra=0.05* self.basic_salary
            self.da=0.1 * self.basic_salary
            self.ta=0.07 * self.basic_salary
            self.tax=0.07 * self.basic_salary
        elif(self.division=='SL'):
         
            self.hra=0.05 * self.basic_salary
            self.da=0.12 * self.basic_salary
            self.ta=0.09 * self.basic_salary    
            self.tax=0.07 * self.basic_salary

        elif(self.division=='RD'):
         
            self.hra=0.1 * self.basic_salary
            self.da=0.1 * self.basic_salary
            self.ta=0.0 * self.basic_salary
            self.tax=0.15 * self.basic_salary
        elif(self.division=='ADM'):
            self.hra=0.15 * self.basic_salary
            self.da=0.2 * self.basic_salary
            self.ta=0.1 * self.basic_salary
            self.tax=0.2 * self.basic_salary
        else:
            print('Invalid option selected') 
          
    def calculate_salary(self):
        self.calculate_allowance()
        self.grosssalary=self.basic_salary+self.hra+self.da+self.ta +self.tax
        self.net_salary=self.grosssalary-self.tax   

    def __str__(self):
        return f'{Employee.__str__(self)}\n\n\n\n\t\t\t*****SALARY SLIP*****\n Basic Salary: {self.basic_salary}\n HRA: {self.hra}\n TA {self.ta}\n DA: {self.da}\n\t\tGross_Salary: {self.grosssalary}\n\t\t Net Salary: {self.net_salary}'    


def main():
    l=[]
    ch='Y'
    while(ch=='Y' or ch=='y'):
        print('**********Welcome to Menu driven program***********')
        print('1. Create or Add Employee')
        print('2. Modify Empployee')
        print('3. View All Employee details')
        print('4. View Employee by EmpId ')
        print('5. Generate Txt file  of Salary file')
        print('6. Generate PDF file  of Salary file')
        
        
        ch=int(input('Enter your Choice'))
        if(ch==1):
            emp=Tax()
            emp.input()
            emp.calculate_salary()
            l.append(emp)

        elif(ch==2):
            print("Please choose the Empid from the below list for which you want to modify inofrmation ")
            for i in l:
                print(i.Ecode)

            c=input("Enter the Employee id from above:   ")
            j=0

            for i in l:
                if(c==i.Ecode):    
                    j=1
                    print('\n1.  To Modify Phone Number Choose P')
                    print('2.   To Modify Address choose A')
                    print('3.   To Modify Salary choose S\n\n')
                    choice=input('Enter the option:    ')
                    if(choice=='A'):
                        addr=input('\nEnter the New Address')
                        i.address=addr
                        
                    elif(choice=='P'):
                        ph=input('\nEnter the New Phone Number')
                        i.phone=ph
                    elif(choice=='S'):
                       sal=input('\n\nEnter the New Salary')
                       i.basic_salary=sal
                    else:
                        print('\n Invalid Choice Entered')
            if(j==0):
                print('\nWrong Employee code Selected') 


                    
            

            
        elif(ch==3):
            j=1
            print('*****List of All the Employee*****')
            for i in l:
                print("*****Employee No.{}***********\n".format(j))

                j+=1
                print(i)
        elif(ch==4):
            empid=input('\n Please Enter Your Emp Id')
            j=0
            for i in l:
                if i.Ecode==empid:
                    j=1
                    print(i)
            if (j==0):
                print('\n\n Oops!  Employee does not Exist')     
        elif(ch==5):
            empid=input('\n Please Enter Your Emp Id')
            j=0
            for i in l:
                if i.Ecode==empid:
                    j=1
                    s=i.Ecode+'_SalarySlip.txt'
                   
                    fd=open(s,"w")
                    s=json.dumps(i.__dict__)
                    print(s)
                    json.dump(s,fd)

            if (j==0):
                print('\n\n Oops!  Employee does not Exist')  

        elif(ch==6):
            empid=input('\n Please Enter Your Emp Id')
            j=0
            for i in l:
                if i.Ecode==empid:
                    j=1
                    s=i.Ecode+'_SalarySlip.pdf'
                   
                    fd=open(s,"w")
                    today=date.today()
                    d1=today.strftime("%d/%m/%Y")
                    fd.write('\n************************************Salary Slip******************************************************')
                    
                    fd.write('\n\n\n\n Emp Name: %s \t\t\t\t\t\t\t Emp No: %s \t\t\t\t Date: %s\n\n\n\n Basic Salary: %.2f \n HRA: %.2f \n TA %.2f \n DA: %.2f \n\n\n\t\t\t\tGross_Salary: %.2f \n\t\t\t\t Net Salary: %.2f'%(i.name,i.Ecode,d1,i.basic_salary,i.hra,i.ta,i.da,i.grosssalary,i.net_salary))    
                    fd.close()

            if (j==0):
                print('\n\n Oops!  Employee does not Exist')         

                       
                    
        else:
             print('Invalid choice entered') 
        
        ch=input('Do you want Enter more(Y/N)')



main()               

            

          
