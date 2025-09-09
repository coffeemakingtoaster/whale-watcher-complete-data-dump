package main

import (
	"archive/tar"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"github.com/google/go-containerregistry/pkg/name"
	v1 "github.com/google/go-containerregistry/pkg/v1"
	"github.com/google/go-containerregistry/pkg/v1/empty"
	"github.com/google/go-containerregistry/pkg/v1/layout"
	"github.com/google/go-containerregistry/pkg/v1/remote"
	"github.com/google/go-containerregistry/pkg/v1/tarball"
)

func main() {
	if len(os.Args) < 3 {
		log.Fatal("Not sufficient")
		return
	}

	image := os.Args[1]
	dockerfileURL := os.Args[2]

	workDir, _ := os.Getwd()
	sanitizedName := strings.ReplaceAll(image, "/", "-")
	sanitizedName = strings.ReplaceAll(sanitizedName, ":", "-")

	targetDir := filepath.Join(workDir, "testdata", sanitizedName)

	if err := os.MkdirAll(targetDir, 0755); os.IsExist(err) {
		log.Fatal("Already exists")
		return
	}

	err := loadImageFromRegistry(image, targetDir)
	if err != nil {
		log.Fatal(err.Error())
	}

	err = downloadDockerfiletoPath(dockerfileURL, targetDir)
	if err != nil {
		log.Fatal(err.Error())
	}

}

func loadImageFromRegistry(image, directory string) error {
	destination := filepath.Join(directory, "oci.tar")
	err := loadTorToPath(image, destination, "oci")
	if err != nil {
		return err
	}

	destinationDocker := filepath.Join(directory, "docker.tar")
	err = loadTorToPath(image, destinationDocker, "docker")
	if err != nil {
		return err
	}
	return nil
}

func loadTorToPath(image, destination, format string) error {
	format = strings.ToLower(format)
	if format != "oci" && format != "docker" {
		return fmt.Errorf("unsupported format: %s (supported: 'oci', 'docker')", format)
	}

	ref, err := name.ParseReference(image)
	if err != nil {
		return err
	}

	platform := v1.Platform{
		Architecture: "amd64",
		OS:           "linux",
	}

	img, err := remote.Image(ref, remote.WithPlatform(platform))
	if err != nil {
		return err
	}

	switch format {
	case "docker":
		fmt.Println("Saving as docker")
		return saveAsDockerTarball(ref, img, destination)
	case "oci":
		fmt.Println("Saving as oci")
		return saveAsOCITarball(img, destination)
	default:
		return fmt.Errorf("unsupported format: %s", format)
	}
}

// saveAsDockerTarball saves the image as a Docker-compatible tarball
func saveAsDockerTarball(ref name.Reference, img v1.Image, destination string) error {
	file, err := os.Create(destination)
	if err != nil {
		return err
	}
	defer file.Close()

	err = tarball.Write(ref, img, file)
	if err != nil {
		return err
	}

	return nil
}

// saveAsOCITarball saves the image as an OCI-compliant tarball
func saveAsOCITarball(img v1.Image, destination string) error {
	// Create a temporary directory for the OCI layout
	tempDir, err := os.MkdirTemp("", "oci-layout-*")
	if err != nil {
		return err
	}

	// Ensure cleanup of temporary directory
	defer func() {
		if removeErr := os.RemoveAll(tempDir); removeErr != nil {
			fmt.Println(err.Error())
		}
	}()

	// Create OCI layout in temp directory
	layoutPath, err := layout.Write(tempDir, empty.Index)
	if err != nil {
		return err
	}

	// Append the image to the layout
	err = layoutPath.AppendImage(img)
	if err != nil {
		return err
	}

	// Create the destination tar file
	file, err := os.Create(destination)
	if err != nil {
		return err
	}
	defer file.Close()

	// Create tar writer (uncompressed)
	tarWriter := tar.NewWriter(file)
	defer tarWriter.Close()

	// Walk through the OCI layout directory and add files to tar
	err = filepath.Walk(tempDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		// Get relative path from temp directory
		relPath, err := filepath.Rel(tempDir, path)
		if err != nil {
			return err
		}

		// Skip the root directory itself
		if relPath == "." {
			return nil
		}

		// Create tar header
		header, err := tar.FileInfoHeader(info, "")
		if err != nil {
			return err
		}
		header.Name = relPath

		// Write header
		err = tarWriter.WriteHeader(header)
		if err != nil {
			return err
		}

		// If it's a regular file, write its content
		if info.Mode().IsRegular() {
			srcFile, err := os.Open(path)
			if err != nil {
				return err
			}
			defer srcFile.Close()

			_, err = io.Copy(tarWriter, srcFile)
			if err != nil {
				return err
			}
		}

		return nil
	})

	if err != nil {
		return err
	}

	return nil
}

func downloadDockerfiletoPath(dockerFileURL, directory string) error {
	// Perform the HTTP GET request
	response, err := http.Get(dockerFileURL)
	if err != nil {
		return err
	}
	defer response.Body.Close()

	targetPath := filepath.Join(directory, "Dockerfile")

	// Create a new local file to write the contents of the remote file
	file, err := os.Create(targetPath)
	if err != nil {
		return err
	}
	defer file.Close()

	// Copy the contents of the remote file to the local file
	_, err = io.Copy(file, response.Body)
	if err != nil {
		return err
	}

	fmt.Printf("Download completed: %s\n", targetPath)
	return nil
}
