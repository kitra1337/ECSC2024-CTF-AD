# APT Finals

| Service    | APT Finals                                                                          |
|:-----------|:------------------------------------------------------------------------------------|
| Authors    | Lorenzo Demenio <@Devrar>, Gianluca Altomani <@devgianlu>                           |
| Stores     | 2                                                                                   |
| Categories | crypto, misc                                                                        |
| Port       | HTTP 8080                                                                           |
| FlagIds    | store1: [match_id], store2: [username]                                              |
| Checkers   | [store1](/checkers/APT-Finals-1/checker), [store2](/checkers/APT-Finals-2/checker)  |

## Description

The service implements a tennis game simulator in Go. A client is provided that allows all the functionalities intended by the server: a user can register, login, create and play matches against a bot and add friends.

At the moment of registration the user also inserts a secret, which will be visible only to friends, which can be added by sending and accepting invitations.

During the tennis matches the client interacts with the server through a web socket. The server decides the destination of the ball and checks that every shot is possible.

When creating a match it is possible to type in a prize for who wins and also the level of difficutly. Since the matches are played randomly, the level of difficulty only decides how far from the center you are able to throw the ball.

## Vulnerabilities

### Store 1 (crypto):

The first flag store is in the prize of the matches created by the checker. These matches are created with difficulty 3, which isn't possible to win playing in the intended way.

Every match has a secret key that is used to derive a point $Q$ on a fixed elliptic curve $E$. Moreover two gaussian distributions $\mathcal{N}_u(0, \sigma_u^2)$ and $\mathcal{N}_b(0, \sigma_b^2)$, with cumulative distribution functions $\Phi_u$ and $\Phi_b$, for the user and the bot are instantiated.

Every time a player hits the ball sends two random numbers $r_1, r_2$ to the server, that are used to compute tow points $P_1 = r_1 \cdot Q$ and $P_2 = r_2 \cdot Q$. These points are used to derive the coordinates $X$ and $Y$ where the ball will be launched to in the following way.

The server computes $p = \frac{P_1x}{2(P_1x + P_1y)}$ as a real number. This is a number in the range $0 < p < 0.5$. Then computes $\Phi_u^{-1}(p)$ (in the case of a client hit), which will be a number in the range $(-\infty, 0)$ distributed relative to $\mathcal{N}_u$. The closer this is to $-\infty$ the further from the center the ball will be launched. The points $P_1$ is used for the $x$-axis and the point $P_2$ for the $y$-axis. Thus, to be able to make good shots, the user must send $r_i$ such that $P_i$ has very small $x$ coordinate.

It is important to notice that the curve $E$ has smooth order, thus the discrete logarithm is easy, and if a player knows $Q$ it can easily compute $r$ such that $rQ$ has small $x$ coordinate.

In level 3 of difficulty, the gaussian distribution $\mathcal{N}_u$ is so narrow that by just taking random points $P_i$ it is impossible to send the ball far enough from the center to score a point.

#### Vuln 1: exploiting 4-torsion points

The curve $E$ has order

$$
n = 2^{20}\cdot 761\cdot 1213\cdot 1471\cdot 2447\cdot 3067\cdot 3947\cdot 4373\cdot 4663\cdot 5189\cdot 7393
$$

thus without knowing $Q$ it is possible to force it in one of the small subgroups by sending $r$ equal to the cofactor. In particular, the points of order $4$ have $x = 1$ and $y \approx n$, giving $p = \frac{1}{2(y+1)}$ very close to 0, thus a shot very far from the center.

Such points can be obtained by sending $r = \frac{n}{4}$.

Fix: check that $rQ$ has not order $4$.

#### Vuln 2: solving the DLP in the small subgroups

When the server returns us the coordinates of where the ball is launched to, we can actually recover $\frac{P_1x}{P_1y}$ and $\frac{P_2x}{P_2y}$, by reversing the operations done by the server.

Let $f$ be one of the factors of $n$. We can force $P_1$ to be in the subgroups of order $f$ by sending $r_1 = \frac{n}{f}$. At this point, knowing $\frac{P_1x}{P_1y}$, we can try every $P \in E[f]$ and check if $\frac{Px}{Py} = \frac{P_1x}{P_1y}$. If this holds with high probability we have $P = P_1$. Doing the same for every $f$, using the CRT we can obtain the original $Q$.

At this point we can win the match as if we know the secret key.

Fix: There are two possible fixes. Either we check that the point $rQ$ is not in any small subgroup, or either we mask the coordinates sent to the client, by still mantaining the fact that a point with small $x$ allows a good shot.

### Store 2 (misc):

Users inside the service can become friends with each other. The friendship is obtained by creating an invite token and
by sharing it another user. Friends can see their respective secret which ultimately contains the flag. Friend requests
are considered pending as long as there's an invite.

An invite is created by encrypting the invitee's username with a randomly generated key that is stored inside the
`friend_invites` table. Simultaneously the username pair is added to the `friends` table.

When an user accepts an invite, the server fetches the key for that username pair, deciphers the invite and checks that
the plaintext is equal to the logged in username. When the key is fetched it is also immediately removed from the
database. If any error occurs the friends entry is also removed.

#### Vuln 1

To exploit this vulnerability, multiple bugs must be chained together:

- When fetching the decryption key from the database the select is erroneously performed both for
  `user_a = $1 and user_b = $2` or `user_a = $2 and user_b = $1` which is not required. This way it is possible to
  trigger the decryption of the invite by providing the victim's username. This won't ever succeed because the final
  check after the decryption will always fail.
- The only way not to call the `RemoveFriend` function is to cause a panic after the decryption key has been removed
  from the database.
- By looking inside the `crypto.DecryptInvite` function we can see that multiple checks are performed on the invite
  length before decoding and decryption.
- The panic can be triggered in the `CryptBlocks` function implementation of the CBC decrypter:

  ```go
  func (x *cbcDecrypter) CryptBlocks(dst, src []byte) {
    if len(src)%x.blockSize != 0 {
        panic("crypto/cipher: input not full blocks")
    }
    if len(dst) < len(src) {
        panic("crypto/cipher: output smaller than input")
    }
    if alias.InexactOverlap(dst[:len(src)], src) {
        panic("crypto/cipher: invalid buffer overlap")
    }
    if len(src) == 0 {
        return
    }
  
    ...
  }
  ```

  Specifically, we can see that a panic will occur if the input is not multiple of the block size.
- However, the check performed before decoding the invite seems to ensure that the Base64 output will be a multiple of
  the block size and therefore prevent the panic.
- In order to have the decode output length mismatch it is needed for the Base64 decode to violate the usual 3/4 ratio.
  This is possible because `DecodeString` will strip all newlines, even in the middle of the string. Those at the start
  and end are trimmed before entering `DecryptInvite`.
- Therefore it is enough to use an invite like `YWFhYWFhYWFhYW\n\nFhYWFh` to cause a panic. The panic will be handled by
  the HTTP server and will not crash the service.
- After this the connection will be closed, but the invite will result accepted. By opening a new connection and listing
  the friends you'll be able to see the flag.

### Vuln 2: unintended

During the competition, teams exploit a simpler variation of the vulnerability by exploiting the race condition between
removing the invite key from the database and removing the friendship when the decryption fails.

It is possible to make the race longer by providing a very long invite that will take a while to decrypt. Considering
the very low latency between the vulnboxes some teams managed to exploit with less noticeable amounts of data.

## Exploits

| Store | Exploit                                                                 |
|:-----:|:------------------------------------------------------------------------|
|   1   | [4tor](/sources/APT-Finals/cmd/exploit4tor/main.go)                     |
|   1   | [SmallSubgroups](/sources/APT-Finals/cmd/exploitSmallSubgroups/main.go) |
|   2   | [exploit2](/sources/APT-Finals/cmd/exploit2/main.go)                    |
