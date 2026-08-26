from langchain_core.tools import tool


@tool
def calculator(first_num: float, second_num: float, operation: str) -> str:
    """
    Perforn basic arthematic operation on two number
    Supported operation add, sub, div, mul
    """
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return "Error: division by zero is not allowed"
            result = first_num / second_num
        else:
            return f"Error: unsupported operation '{operation}'. Use add, sub, mul or div"

        return f"{first_num} {operation} {second_num} = {result}"
    except Exception as e:
        return f"Error: {e}"
