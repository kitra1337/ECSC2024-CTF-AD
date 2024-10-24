package apt

const (
	UsernameMinLength = 8
	PasswordLength    = 16
)

// Don't change these to keep your SLA
const (
	CourtWidth  = 1200
	CourtHeight = 600

	PlayerWidth  = 20
	PlayerHeight = 60
	PlayerSpeed  = 300

	BallRadius              = 10
	BallAcceleration        = 1000000.0
	BallFirstBounceDuration = 1.0
	BallBounceFactor        = 0.8
	BallMaxBounces          = 4
	BallCollisionFactor     = 0.5
	BallStartX              = 100
	BallStartY              = CourtHeight / 2

	ClientStartX = 40
	ClientStartY = CourtHeight / 2

	BotStartX = CourtWidth / 4 * 3
	BotStartY = CourtHeight / 8 * 3
)

var (
	DifficultiesClient = []float64{400, 400, 100, 10}
	DifficultiesBot    = []float64{200, 400, 300, 100}
)
