import numpy as np

def get_ppo_position_size(confidence_score: float) -> float:
    """
    This function would load a pre-trained PPO agent and use it to
    determine the optimal position size.
    
    For now, it returns a placeholder value based on a simple rule.
    This simulates what an RL agent would learn to do: take larger positions
    when confidence is high and smaller positions when it's low.
    
    :param confidence_score: The final confidence from the main model (0.0 to 1.0).
    :return: A position size from -1.0 (Short) to 1.0 (Long).
    """
    # A simple linear mapping from confidence to position size.
    # Assumes 0.5 is neutral.
    # Confidence > 0.5 -> Long position
    # Confidence < 0.5 -> Short position
    
    # Scale the confidence (0 to 1) to a position size (-1 to 1)
    # This makes the position size proportional to the deviation from neutral.
    position_size = (confidence_score - 0.5) * 2.0
    
    # Clamp the value to be strictly within [-1.0, 1.0]
    return float(np.clip(position_size, -1.0, 1.0))