# Python has no built-in ceiling operator, and Math.ceil is not recommended for integer division:
# https://stackoverflow.com/a/17511341 
def ceildiv(a, b):
    return -(a // -b)

# Helpers for printing loading / progress bar on command line
def print_loading_header() -> None:
    print('=====================> 25% ===================> 50% ===================> 75% ===================> 100%')

# Assumes batch_number is 0-based, so the final batch_number is total_batches - 1
def print_loading_dot(batch_number: int, total_batches: int) -> None:
    if batch_number < 0:
        return

    old_int_percent = batch_number * 100 // total_batches
    new_int_percent = (batch_number+1) * 100 // total_batches
    for _ in range(new_int_percent - old_int_percent):
        print('.', end='', flush=True)
    
    if batch_number == total_batches-1:
        print('', flush=True) # Final batch, print a newline