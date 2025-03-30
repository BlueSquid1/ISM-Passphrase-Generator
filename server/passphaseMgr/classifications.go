package passphaseMgr

type Classification int

//go:generate stringer -type=Classification
const (
	Protected Classification = iota
	Secret
	TopSecret
)

var MapEnumStringToClassification = func() map[string]Classification {
	m := make(map[string]Classification)
	for i := Protected; i <= TopSecret; i++ {
		m[i.String()] = i
	}
	return m
}()
