# OpenFOAM Learning

This repository contains an OpenFOAM case that performs an automated sweep over various angles of attack for a **NACA 0012 airfoil** at **Re = 1000**.

The case is written for **OpenFOAM 13**.

## Clone the Repository

```bash
git clone https://github.com/Imdadullah-Raji/openfoam-learning.git
```

## Running the Simulation

Navigate to the repository, make the script executable, and run it:

```bash
cd openfoam-learning
chmod +x runSweep.sh
./runSweep.sh
```

## Notes

- Ensure **OpenFOAM 13** is installed and its environment is sourced before running the script.
- The repository contains the case setup only; generated simulation data are intentionally excluded from version control.



