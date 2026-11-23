# Isolated runtime for squad tests: Claude Code + a common dev toolchain + the
# Multica CLI/daemon, so agent runs happen here and not on the host.
FROM ubuntu:24.04
ARG GO_VERSION=1.27.4
ARG NODE_MAJOR=22
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl wget gnupg git openssh-client build-essential pkg-config \
      python3 python3-pip python3-venv pipx jq ripgrep fd-find tree unzip zip xz-utils \
      make cmake sqlite3 procps less vim-tiny sudo tini \
    && rm -rf /var/lib/apt/lists/*

# GitHub CLI
RUN mkdir -p -m 755 /etc/apt/keyrings \
 && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg -o /etc/apt/keyrings/githubcli.gpg \
 && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/githubcli.gpg] https://cli.github.com/packages stable main" > /etc/apt/sources.list.d/github-cli.list \
 && apt-get update && apt-get install -y gh && rm -rf /var/lib/apt/lists/*

# Go
RUN curl -fsSL https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz | tar -C /usr/local -xz
# Node + Claude Code
RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_MAJOR}.x | bash - \
 && apt-get install -y nodejs && rm -rf /var/lib/apt/lists/* \
 && npm install -g @anthropic-ai/claude-code

COPY bin/multica /usr/local/bin/multica
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

# Non-root user; the default Ubuntu user (uid 1000) is replaced.
RUN userdel -r ubuntu 2>/dev/null; useradd -m -u 1000 -s /bin/bash agent \
 && echo 'agent ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/agent
USER agent
ENV HOME=/home/agent \
    PATH=/home/agent/go/bin:/usr/local/go/bin:/home/agent/.local/bin:$PATH \
    MULTICA_WORKSPACES_ROOT=/home/agent/multica_workspaces
# Neutral commit identity: agent commits never carry a person's address.
RUN git config --global user.name "squad-runtime" \
 && git config --global user.email "squad-runtime@multica.local" \
 && git config --global init.defaultBranch main \
 && git config --global credential.helper '!gh auth git-credential' \
 && mkdir -p ~/.claude ~/multica_workspaces ~/.multica
WORKDIR /home/agent

# --no-auto-update/--no-auto-reload: keep the CLI pinned to the server's version.
ENTRYPOINT ["tini","--","/usr/local/bin/entrypoint.sh"]
CMD ["multica","daemon","start","--foreground","--no-auto-update","--no-auto-reload"]
