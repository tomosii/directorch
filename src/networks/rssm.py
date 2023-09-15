import torch
from torch import nn
from torch import Tensor


class RSSM(nn.Module):
    """Recurrent State Space Model."""

    def __init__(
        self,
    ):
        super().__init__()
        self.representation_model = RepresentationModel()
        self.transition_model = TransitionModel()


class RepresentationModel(nn.Module):
    """
    Infer the stochastic state (z) from the embed observation (o) and the deterministic state (h).

    z ~ p(z|o, h)

    ### Input:
    - Embed observation (o) : observation after encoding
    - Deterministic state (h)

    ### Output:
    - Gaussian distribution of stochastic state (z)

    Agent tries to infer the current state using both past information and current observation.
    """

    def __init__(
        self,
        embeded_observation_size: int,
        deterministic_state_size: int,
        stochastic_state_size: int,
        hidden_size: int,
    ):
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(embeded_observation_size + deterministic_state_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, stochastic_state_size * 2),
            # Outputs mean and std for gaussian distribution
        )

    def forward(self, embeded_o: Tensor, deter_h: Tensor) -> Tensor:
        x = torch.cat([embeded_o, deter_h], dim=-1)
        x = self.network(x)

        # Split concatenated output into mean and standard deviation
        mean, std = torch.chunk(x, 2, dim=-1)

        # Apply softplus to std to ensure it is positive
        # Add min_std for numerical stability
        min_std = 0.1
        std = torch.nn.functional.softplus(std) + min_std

        # Create gaussian distribution
        distribution = torch.distributions.Normal(mean, std)
        return distribution


class TransitionModel(nn.Module):
    """
    Predict the stochastic state (z) from the deterministic state (h) without observation (o).

    z ~ p(z|h)

    ### Input:
      - Deterministic state (h)

    ### Output:
    - Gaussian distribution of stochastic state (z)

    Agent predicts z^ only using h that includes past information, without seeing o. (Imagination)
    """

    def __init__(
        self,
        deterministic_state_size: int,
        stochastic_state_size: int,
        hidden_size: int,
    ):
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(deterministic_state_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, stochastic_state_size * 2),
            # Outputs mean and std for gaussian distribution
        )

    def forward(self, deter_h: Tensor) -> Tensor:
        x = self.network(deter_h)

        # Split concatenated output into mean and standard deviation
        mean, std = torch.chunk(x, 2, dim=-1)

        # Apply softplus to std to ensure it is positive
        # Add min_std for numerical stability
        min_std = 0.1
        std = torch.nn.functional.softplus(std) + min_std

        # Create gaussian distribution
        distribution = torch.distributions.Normal(mean, std)
        return distribution


class RecurrentModel(nn.Module):
    """
    Output the next deterministic state (h_t) from the previous deterministic state (h_t-1), stochastic state (z_t-1), and action (a_t-1).

    h_t ~ p( h_t | h_t-1, z_t-1, a_t-1 )

    ### Input:
    - Previous deterministic state (h_t-1)
    - Previous stochastic state (z_t-1)
    - Previous action (a_t-1)

    ### Output:
    - Next deterministic state (h_t)
    """

    def __init__(
        self,
        deterministic_state_size: int,
        stochastic_state_size: int,
        action_size: int,
        hidden_size: int,
    ):
        super().__init__()

        self.input_network = nn.Sequential(
            nn.Linear(stochastic_state_size + action_size, hidden_size),
            nn.ReLU(),
        )
        self.rnn = nn.GRUCell(hidden_size, deterministic_state_size)

    def forward(self, stoch_z: Tensor, action: Tensor, deter_h: Tensor) -> Tensor:
        x = torch.cat([stoch_z, action], dim=-1)
        x = self.input_network(x)

        # Input the new input and previous hidden state to the RNN
        next_deter_h = self.rnn(x, deter_h)
        return next_deter_h
