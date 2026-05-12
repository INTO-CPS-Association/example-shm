from typing import Optional, Any
from datetime import datetime

def eof_rul(result: dict[str, Any], time_passed: datetime, output_time_unit: Optional[str] = "hrs", damage_sum: Optional[float] = 1) -> tuple[float,float]:
        """End of life (EOF) or endurable life and Remaining useful life (RUL)

        Example 1:
        time_passed = 24 hr
        D_t = 0.1

        EOF = 240 hr #The end of life is at 240 hours
        RUL = (time_passed - EOF) = 226 hr #Remaining useful life (RUL) is then 226 hours

        Example 2:
        time_passed = 1,000,000 cycles
        D_t = 0.2

        EOF = 5,000,000 cycles #The end of life is at 5 mio. cycles.
        RUL = (time_passed - EOF) = 4,000,000 cycles #Remaining useful life (RUL) is then 4 mio. cycles
        
        Args:
            result (dict): Dictionary of results from continous data stream.
                - 'D_t' (float): New damage applied
            time_passed (int/datetime.timedelta): Specified cycles or time passed
            output_time_unit (int/datetime): Output unit for cycles or time       
        
        Returns:
            EOF (float): End of life (EOF) or endurable life
            RUL (float): Remaining useful life (RUL) 
        """

        d_tot = result["D_t"]

        if output_time_unit == "years":
            years = time_passed.days/365.25
            seconds = time_passed.seconds
            years_seconds = seconds/60/60/24/365.25
            time_elapsed = years + years_seconds
            
        elif output_time_unit == "days":
            days = time_passed.days
            seconds = time_passed.seconds
            days_seconds = seconds/60/60/24
            time_elapsed = days + days_seconds
        
        elif output_time_unit == "hrs":
            hr = time_passed.days*24
            seconds = time_passed.seconds
            hr_seconds = seconds/60/60
            time_elapsed = hr + hr_seconds
        
        elif output_time_unit == "cycles":
            time_elapsed = time_passed
        
        EOF = time_elapsed / (d_tot/damage_sum)
        RUL = EOF - time_elapsed

        return EOF, RUL